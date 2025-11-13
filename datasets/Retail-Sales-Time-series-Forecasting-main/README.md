# **Retail Sales Time-series Forecasting**

**Project By: GANESH KASTURI**

**Introduction:**

In the increasingly competitive fashion retail industry, companies are constantly adopting strategies focused on adjusting the products characteristics to closely satisfy customers&#39; requirements and preferences. Although the lifecycles of fashion products are very short, the definition of inventory and purchasing strategies can be supported by the large amounts of historical data which are collected and stored in companies&#39; databases. This study explores the use of a deep learning approach to forecast sales in fashion industry, predicting the sales of new individual products in future seasons. This study aims to support a fashion retail company in its purchasing operations and consequently the dataset under analysis is a real dataset provided by this company.

**Data Preparation:**

In order to make sure that the experiments are conducted in a consistent way, before applying any method, it is necessary to prepare the data. Formally data preparation involves data discretization, data cleaning, data integration, data transformation and data reduction.

- **Data Gathering:**

**Data Set 1**** :**Rossmann store managers are tasked with predicting their daily sales for up to six weeks in advance. Store sales are influenced by many factors, including promotions, competition, school and state holidays, seasonality, and locality. With thousands of individual managers predicting sales based on their unique circumstances, the accuracy of results can be quite varied.

**Data Set 2**** :**  Walmart runs several promotional markdown events throughout the year. These markdowns precede prominent holidays, the four largest of which are the Super Bowl, Labour Day, Thanksgiving, and Christmas. The weeks including these holidays are weighted five times higher in the evaluation than non-holiday weeks. Part of the challenge presented by this competition is modelling the effects of markdowns on these holiday weeks in the absence of complete/ideal historical data.

This file contains anonymized information about the 45 stores, indicating the type and size of store.

**Missing Data Handling:**

Missing data is a problem because it adds ambiguity to your analysis. Consider the data in the table above. What if you want to find out the average number of employees? With the second observation missing a data value, it would be impossible to accurately work it out. You could work around this by computing the average based on the available data, but your results will always be flawed. Furthermore, an observation that has missing data for a variable indicates that it is atypical. Therefore, any analysis that assumes the missing value fits neatly into the rest of the data, is unsound.

You have three options when dealing with missing data. The most obvious and by far the easiest option, is to simply ignore any observations that have missing values. This is often called _complete case _analysis or _listwise deletion _of missing values.

Another approach is to _impute _the missing values. This involves using statistical or machine learning models to make educated guesses based about the values of the missing data. For example, you could create a model that predicts the number of employees based on the other variables and then use this model to predict the number of employees. A variant of this approach, known as _multiple imputation, _is usually considered best practice when building regression-type models (e.g., linear regression, logistic regression).

- From the Dataset we have came up that there a lot of missing values present in the dataset.

![](RackMultipart20210617-4-1hq6ua7_html_ac4c218248e9eafb.png)

-
# **Fill NaN values**

## Filling up &#39;Promo2SinceWeek&#39;,&#39;Promo2SinceYear&#39;,&#39;PromoInterval&#39; columns

## ![](RackMultipart20210617-4-1hq6ua7_html_d9fea57ab131802a.png)

-
# Filling up &#39;CompetitionOpenSinceMonth&#39;,&#39;CompetitionOpenSinceYear&#39;

![](RackMultipart20210617-4-1hq6ua7_html_4514b1b25ab67c41.png)

**Feature engineering**

Feature engineering is the process of transforming raw data into features that better represent the underlying problem to the predictive models, resulting in improved model accuracy on unseen data. Feature engineering turn your inputs into things the algorithm can understand.

- We have used **One hot encoding.**
- **Encoding for Binary data.**

Binary encoding is a combination of Hash encoding and one-hot encoding. In this encoding scheme, the categorical feature is first converted into numerical using an ordinal encoder. Then the numbers are transformed in the binary number. After that binary value is split into different columns.

- **Encoding for nominal data**

Machine learning models require all input and output variables to be numeric. This means that if your data contains categorical data, you must encode it to numbers before you can fit and evaluate a model. The two most popular techniques are an Ordinal Encoding and a One-Hot Encoding.

- **Convert/Manage Date column**

Dealing with Date and parse each element of a date is crucial in order to analyses event.

First things with we need to convert our Date column (often considered as a string column with pandas). One of the most important field is to know how to use the format parameters.

**Exploratory Data analysis**

Beyond focusing on a single variable, it is quite desirable to analyse whole population, in which statistical variables are jointly considered. To this end, exploratory data analysis serves approaches to cover these information. Essentially underlying the exploratory data analysis is possible to measure the dependency between statistical variables, which makes the analysis more understandable. The key difference between the descriptive and the exploratory analysis is actually the way to handle the variables.

In this regard, correlation analysis, principal component analysis (PCA), box plot, vector quantization (VQ), scatter plot and matrix factorization are relevant tools in this field.

**Sales**

![](RackMultipart20210617-4-1hq6ua7_html_1f959ce53d8737e0.png) ![](RackMultipart20210617-4-1hq6ua7_html_706514908cd8708d.png)

**Plotting sales distribution plot for different stores.**

![](RackMultipart20210617-4-1hq6ua7_html_de53434815820905.png)

**For different stores:**

![](RackMultipart20210617-4-1hq6ua7_html_40225ea818fb14a0.png)

**Autocorrelation plot for store**

![](RackMultipart20210617-4-1hq6ua7_html_6f12bf53a583cfd7.png)

**Day of Week:**

![](RackMultipart20210617-4-1hq6ua7_html_9ca758f6c3845ba2.png)

**State Holiday**

![](RackMultipart20210617-4-1hq6ua7_html_24e8a5e535b7d38d.png)

# **Heatmap of Correlation in numerical values**

![](RackMultipart20210617-4-1hq6ua7_html_4acd16cf97fd0597.png)

**Model Building(TIME SERIES MODELS)**

![](RackMultipart20210617-4-1hq6ua7_html_a65ec9d7b81e5447.png)

![](RackMultipart20210617-4-1hq6ua7_html_3cd44f5caabe90ff.png)

![](RackMultipart20210617-4-1hq6ua7_html_9c65f897c23eaf6a.png)

![](RackMultipart20210617-4-1hq6ua7_html_230b9f877c4af41e.png)

**Model Implementation:**

![](RackMultipart20210617-4-1hq6ua7_html_5a3f97cf41b74d92.png)

![](RackMultipart20210617-4-1hq6ua7_html_367dce5de1fdd3e2.png)

![](RackMultipart20210617-4-1hq6ua7_html_28bd989c90f99599.png)

-
##
-

**jj**

