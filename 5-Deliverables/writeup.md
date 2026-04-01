# Telco Churn Prediction — Results Writeup

## Exploratory Analysis

### Feature 1: Contract Type
Customers on month-to-month contracts churn at a dramatically higher rate than those on longer-term contracts. Month-to-month customers represent the vast majority of churned customers, while one-year and two-year contract holders show very low churn rates. This makes intuitive sense — longer contracts create switching costs and signal a higher level of commitment from the customer.

### Feature 2: Tenure
The tenure density plot shows a clear pattern: churned customers skew heavily toward shorter tenures (0–20 months), while retained customers are more evenly distributed and peak at longer tenures. This means new customers are at the highest risk of leaving, and customers who stay past ~24 months become significantly more stable.

**Key EDA takeaway:** New customers on month-to-month contracts are the highest-risk segment. Retention efforts should be front-loaded toward this group.

---

## Model

A **Random Forest** classifier was trained on 80% of the data (5,627 samples) and evaluated on the held-out 20% (1,405 samples).

**Why Random Forest?**
The dataset contains a mix of numeric features (tenure, MonthlyCharges) and categorical features (Contract, PaymentMethod, InternetService, etc.) with non-linear interactions. Random Forest handles this natively without dummy encoding or feature scaling, and provides feature importance scores for free.

**Do we need a validation set?**
No. Random Forest uses out-of-bag (OOB) error estimation internally — each tree is evaluated on the samples not used to train it, giving an unbiased error estimate equivalent to cross-validation. The OOB error rate was **19.51%**. A separate validation set is only needed when tuning hyperparameters with a grid search.

### Results on Test Set

| Metric    | Value |
|-----------|-------|
| Accuracy  | 79.0% |
| Precision | 0.651 |
| Recall    | 0.450 |
| F1 Score  | 0.532 |

**Confusion matrix:**
- True Negatives (correctly predicted stayed): 942
- True Positives (correctly predicted churned): 168
- False Positives (predicted churn, actually stayed): 90
- False Negatives (missed churners): 205

Recall (0.45) is lower than precision (0.65), meaning the model misses about half of actual churners. This is a known trade-off — the model is conservative and prefers not to flag loyal customers incorrectly.

### Top Predictive Features

1. TotalCharges
2. MonthlyCharges
3. Tenure
4. Contract type
5. OnlineSecurity / TechSupport

Financial features (charges, tenure) dominate, confirming the EDA findings.

---

## Recommended Course of Action

1. **Target month-to-month customers in their first 12 months** with proactive outreach. Offer discounts for upgrading to a 1-year contract — this is the single highest-impact intervention based on the feature importance and EDA.

2. **Flag customers with high monthly charges and no add-on services** (no OnlineSecurity, no TechSupport). These customers are paying a lot but getting little value, making them price-sensitive churners. Offer bundled service packages at a discount.

3. **Use the model's churn probabilities, not just the binary prediction.** Customers with high churn probability but who haven't yet churned are the best targets for retention incentives — they are still reachable. The cost of a discount offer is far lower than the cost of losing a customer entirely.

4. **Accept the recall/precision trade-off deliberately.** If retention incentives are cheap (e.g., a one-time discount), lower the decision threshold to catch more churners at the cost of some false positives. If incentives are expensive, keep the threshold high and target only high-confidence predictions.
