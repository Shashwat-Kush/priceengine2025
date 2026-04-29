import torch
import torch.nn as nn
import pytorch_lightning as pl

class ParamPredictor(pl.LightningModule):
    def __init__(self, input_dim, output_dim):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, 256),
            nn.LayerNorm(256),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(256, 128),
            nn.ReLU(),
            nn.Linear(128, output_dim)
        )
        # Higher weight on beta1 (price elasticity) - most important param
        self.loss_weights = torch.ones(output_dim)
        if output_dim > 1:
            self.loss_weights[1] = 5.0   # index 1 = beta1

    def forward(self, x): 
        return self.net(x)

    def training_step(self, batch, _):
        x, y = batch
        pred = self(x)
        # Move weights to correct device if needed
        self.loss_weights = self.loss_weights.to(pred.device)
        loss = ((pred - y)**2 * self.loss_weights).mean()
        self.log('train_loss', loss)
        return loss

    def configure_optimizers(self):
        return torch.optim.Adam(self.parameters(), lr=1e-3, weight_decay=1e-4)
