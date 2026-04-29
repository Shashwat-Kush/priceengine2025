import matplotlib.pyplot as plt
import seaborn as sns
import shap
import os
from src.utils.config import FIGURES_DIR

def plot_actual_vs_predicted(y_true, y_pred, segment_labels=None, title=''):
    fig, ax = plt.subplots(figsize=(8, 6))
    if segment_labels is not None:
        sc = ax.scatter(y_true, y_pred, c=segment_labels, cmap='viridis',
                        alpha=0.6, edgecolors='none', s=20)
        plt.colorbar(sc, ax=ax, label='Price Segment')
    else:
        ax.scatter(y_true, y_pred, alpha=0.6, edgecolors='none', s=20)
        
    ax.plot([y_true.min(), y_true.max()],
            [y_true.min(), y_true.max()], 'r--', lw=1.5, label='Perfect')
    ax.set_xlabel('Actual Units Sold')
    ax.set_ylabel('Predicted Units Sold')
    ax.set_title(title)
    plt.tight_layout()
    os.makedirs(FIGURES_DIR, exist_ok=True)
    plt.savefig(os.path.join(FIGURES_DIR, 'actual_vs_predicted.png'), dpi=150)
    plt.close()

def plot_feature_importance(model, X_test, feature_names):
    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(X_test)
    shap.summary_plot(shap_values, X_test, feature_names=feature_names, show=False)
    plt.tight_layout()
    os.makedirs(FIGURES_DIR, exist_ok=True)
    plt.savefig(os.path.join(FIGURES_DIR, 'shap_summary.png'), dpi=150)
    plt.close()

def plot_elasticity_dist(elasticity_values, labels=None):
    fig, ax = plt.subplots(figsize=(8, 6))
    if labels is not None:
        sns.histplot(x=elasticity_values, hue=labels, multiple='stack', ax=ax)
    else:
        sns.histplot(elasticity_values, ax=ax)
    ax.set_xlabel('Price Elasticity (beta1)')
    ax.set_title('Distribution of Price Elasticity across SKUs')
    plt.tight_layout()
    os.makedirs(FIGURES_DIR, exist_ok=True)
    plt.savefig(os.path.join(FIGURES_DIR, 'elasticity_dist.png'), dpi=150)
    plt.close()

def plot_seasonality_heatmap(seasonality_matrix, index_labels, columns_labels):
    fig, ax = plt.subplots(figsize=(10, 8))
    sns.heatmap(seasonality_matrix, yticklabels=index_labels, xticklabels=columns_labels, cmap='coolwarm', ax=ax)
    ax.set_title('Seasonality Heatmap')
    plt.tight_layout()
    os.makedirs(FIGURES_DIR, exist_ok=True)
    plt.savefig(os.path.join(FIGURES_DIR, 'seasonality_heatmap.png'), dpi=150)
    plt.close()

def plot_model_comparison(models, metrics):
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.bar(models, metrics)
    ax.set_ylabel('MAPE')
    ax.set_title('Model Comparison')
    plt.tight_layout()
    os.makedirs(FIGURES_DIR, exist_ok=True)
    plt.savefig(os.path.join(FIGURES_DIR, 'model_comparison.png'), dpi=150)
    plt.close()
