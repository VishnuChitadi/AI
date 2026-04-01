.libPaths('~/R/library')

library(tidyverse)
library(caret)
library(randomForest)

set.seed(42)

# ── 1. Load and clean ─────────────────────────────────────────────────────────
df <- read_csv("WA_Fn-UseC_-Telco-Customer-Churn.csv", show_col_types = FALSE)

df <- df %>%
  select(-customerID) %>%
  mutate(
    TotalCharges  = suppressWarnings(as.numeric(TotalCharges)),
    SeniorCitizen = factor(ifelse(SeniorCitizen == 1, "Yes", "No")),
    Churn         = factor(Churn, levels = c("No", "Yes"))
  ) %>%
  drop_na()

cat("Rows after cleaning:", nrow(df), "\n")
cat("Churn balance:\n"); print(table(df$Churn))


# ── 2. EDA ────────────────────────────────────────────────────────────────────

# Plot 1: Churn rate by contract type
contract_rates <- df %>%
  group_by(Contract, Churn) %>%
  summarise(n = n(), .groups = "drop") %>%
  group_by(Contract) %>%
  mutate(pct = n / sum(n) * 100)

png("plot_01_contract_churn.png", width = 800, height = 550, res = 120)
ggplot(contract_rates, aes(x = Contract, y = pct, fill = Churn)) +
  geom_col(position = "stack", width = 0.6) +
  geom_text(aes(label = sprintf("%.1f%%", pct)),
            position = position_stack(vjust = 0.5), size = 3.5, color = "white") +
  scale_fill_manual(values = c("No" = "#377EB8", "Yes" = "#E41A1C")) +
  labs(title = "Churn Rate by Contract Type",
       x = "Contract Type", y = "Percentage of Customers (%)", fill = "Churned") +
  theme_minimal(base_size = 13)
dev.off()
cat("Saved plot_01_contract_churn.png\n")

# Plot 2: Tenure distribution by churn status
png("plot_02_tenure_churn.png", width = 800, height = 550, res = 120)
ggplot(df, aes(x = tenure, fill = Churn, color = Churn)) +
  geom_density(alpha = 0.45, linewidth = 0.8) +
  scale_fill_manual(values  = c("No" = "#377EB8", "Yes" = "#E41A1C")) +
  scale_color_manual(values = c("No" = "#377EB8", "Yes" = "#E41A1C")) +
  labs(title = "Customer Tenure by Churn Status",
       x = "Tenure (months)", y = "Density", fill = "Churned", color = "Churned") +
  theme_minimal(base_size = 13)
dev.off()
cat("Saved plot_02_tenure_churn.png\n")


# ── 3. Train / test split (80/20, stratified) ─────────────────────────────────
train_idx <- createDataPartition(df$Churn, p = 0.8, list = FALSE)
train <- df[ train_idx, ]
test  <- df[-train_idx, ]

cat("\nTrain size:", nrow(train), " | Test size:", nrow(test), "\n")


# ── 4. Random Forest model ────────────────────────────────────────────────────
cat("\nTraining Random Forest (ntree=500)...\n")
rf_model <- randomForest(Churn ~ ., data = train, ntree = 500, importance = TRUE)
cat("OOB error rate:", round(rf_model$err.rate[500, "OOB"] * 100, 2), "%\n")


# ── 5. Evaluate on test set ───────────────────────────────────────────────────
preds <- predict(rf_model, newdata = test)
cm    <- confusionMatrix(preds, test$Churn, positive = "Yes")

cat("\n── Test Set Results ─────────────────────────────────\n")
print(cm)

precision <- cm$byClass["Pos Pred Value"]
recall    <- cm$byClass["Sensitivity"]
f1        <- cm$byClass["F1"]
cat(sprintf("\nPrecision : %.3f\n", precision))
cat(sprintf("Recall    : %.3f\n", recall))
cat(sprintf("F1 Score  : %.3f\n", f1))

# Confusion matrix heatmap
cm_df <- as.data.frame(cm$table)
colnames(cm_df) <- c("Predicted", "Actual", "Count")

png("plot_03_confusion_matrix.png", width = 600, height = 500, res = 120)
ggplot(cm_df, aes(x = Predicted, y = Actual, fill = Count)) +
  geom_tile(color = "white") +
  geom_text(aes(label = Count), size = 7, fontface = "bold") +
  scale_fill_gradient(low = "#D6EAF8", high = "#1A5276") +
  labs(title = "Confusion Matrix — Random Forest",
       subtitle = sprintf("Precision: %.3f  |  Recall: %.3f  |  F1: %.3f",
                          precision, recall, f1)) +
  theme_minimal(base_size = 13)
dev.off()
cat("Saved plot_03_confusion_matrix.png\n")


# ── 6. Feature importance ─────────────────────────────────────────────────────
cat("\n── Top 10 Features by Mean Decrease Gini ────────────\n")
imp <- importance(rf_model) %>%
  as.data.frame() %>%
  rownames_to_column("Feature") %>%
  arrange(desc(MeanDecreaseGini)) %>%
  head(10)
print(imp[, c("Feature", "MeanDecreaseGini")])
