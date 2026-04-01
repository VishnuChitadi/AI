# Telco Churn Prediction — Implementation Plan

## Language & Folder

- Language: **R**
- Data: `../5-Deliverables/WA_Fn-UseC_-Telco-Customer-Churn.csv`
- All output (plots + writeup) saved in `6-Deliverables/`

## Folder Structure

```
/workspaces/AI/6-Deliverables/
├── plan.md                        # This file
├── churn.R                        # Main analysis script
├── writeup.md                     # Summary writeup
│
├── plot_01_contract_churn.png     # EDA: contract type vs churn rate
├── plot_02_tenure_churn.png       # EDA: tenure distribution vs churn
└── plot_03_confusion_matrix.png   # Model: confusion matrix heatmap
```

## R Packages

- `tidyverse` — data loading, wrangling, ggplot2 for plots
- `caret` — train/test split, model training, confusion matrix
- `randomForest` — the predictive model

## Implementation Order

### Step 1 — Load and Clean Data
- Read CSV with `read_csv()`
- Drop `customerID` column (not a feature)
- Convert `Churn` from "Yes"/"No" to a factor with levels `c("No", "Yes")`
- Convert `SeniorCitizen` from 0/1 integer to a factor (`"No"/"Yes"`)
- `TotalCharges` has a few blank strings that need coercing to `NA`, then impute or drop those rows (only ~11 rows)

### Step 2 — Exploratory Analysis

**Feature 1: Contract type vs. churn rate**
Bar chart showing churn rate (% churned) for each contract type:
Month-to-month, One year, Two year. Hypothesis: month-to-month customers
churn far more. Use `geom_bar(position="fill")` or compute rates manually
and use `geom_col`. Save as `plot_01_contract_churn.png`.

**Feature 2: Tenure vs. churn**
Overlapping density plot (or violin) of tenure grouped by Churn Yes/No.
Hypothesis: newer customers churn more. Use `geom_density(alpha=0.5)`.
Save as `plot_02_tenure_churn.png`.

### Step 3 — Train/Test Split
Use `caret::createDataPartition(y, p=0.8, list=FALSE)` to split 80/20,
stratified on the `Churn` label so class balance is preserved in both sets.

### Step 4 — Model: Random Forest
Use `randomForest::randomForest(Churn ~ . - customerID, data=train, ntree=500)`.

**Why Random Forest?**
- Handles a mix of categorical and numeric features without dummy encoding
- Naturally captures non-linear interactions (e.g. high charges + month-to-month)
- Provides feature importance scores for free
- Robust to outliers and doesn't require feature scaling

**Do we need a validation set?**
No. Random forests use out-of-bag (OOB) error estimation internally, which
acts as a built-in cross-validation over the training set. We use the test
set only for final evaluation. A separate validation set would only be
needed if we were tuning hyperparameters with a grid search.

### Step 5 — Evaluate on Test Set
- Predict on test set: `predict(model, newdata=test)`
- Compute confusion matrix: `caret::confusionMatrix(pred, test$Churn, positive="Yes")`
- Report: **confusion matrix**, **precision** (Pos Pred Value), **recall** (Sensitivity)
- Also report accuracy and F1 for completeness
- Save a heatmap of the confusion matrix as `plot_03_confusion_matrix.png`

### Step 6 — Feature Importance
Print a feature importance table from `importance(model)` showing which
variables most drive churn prediction (expected top features: Contract,
tenure, MonthlyCharges, TotalCharges).

### Step 7 — Writeup (`writeup.md`)
Short writeup covering:
1. **EDA findings** — what the two plots show about which customers churn
2. **Model summary** — why random forest, what the metrics mean
3. **Recommended course of action** — who to target for retention offers
   based on the model's findings (e.g. flag month-to-month customers in
   their first 12 months with high monthly charges)

## Key Design Decisions

- **Random forest over logistic regression**: the dataset has many categorical
  features with 3+ levels and likely non-linear interactions; RF handles this
  natively and gives better predictive performance
- **Stratified split**: churn is imbalanced (~26% Yes); stratification ensures
  the test set reflects the same ratio
- **Positive class = "Yes" (churned)**: recall matters more than precision here
  — missing an at-risk customer (false negative) is costlier than offering a
  discount to a loyal one (false positive)
- **No validation set**: OOB error from RF serves this role on the training data
