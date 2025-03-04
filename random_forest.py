
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score
import matplotlib.pyplot as plt
import seaborn as sns

# 1. Load Your Data
# Replace 'silk_data.csv' with your actual data file.
df = pd.read_csv('silk_data.csv')

# Assume your dataset has already been preprocessed and includes a 'label' column
# where 0 = benign and 1 = DDoS attack.
# You may need to engineer additional features depending on your raw data.

# 2. Define Features and Labels
# Drop any non-feature columns as needed.
X = df.drop('label', axis=1)
y = df['label']

# 3. Split Data into Training and Testing Sets
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

# 4. Initialize and Train a Baseline Random Forest Model
rf = RandomForestClassifier(n_estimators=100, random_state=42, class_weight='balanced')
rf.fit(X_train, y_train)

# 5. Evaluate the Baseline Model
y_pred = rf.predict(X_test)
print("Classification Report:\n", classification_report(y_test, y_pred))
print("Confusion Matrix:\n", confusion_matrix(y_test, y_pred))
print("ROC AUC Score:", roc_auc_score(y_test, rf.predict_proba(X_test)[:, 1]))

# 6. Hyperparameter Tuning using GridSearchCV
param_grid = {
    'n_estimators': [100, 200, 500],
    'max_depth': [None, 10, 20, 30],
    'min_samples_split': [2, 5, 10],
    'min_samples_leaf': [1, 2, 4],
    'bootstrap': [True, False]
}

grid_search = GridSearchCV(
    estimator=rf,
    param_grid=param_grid,
    cv=3,
    n_jobs=-1,
    verbose=2,
    scoring='roc_auc'
)
grid_search.fit(X_train, y_train)

print("Best Hyperparameters:", grid_search.best_params_)

# 7. Evaluate the Tuned Model
best_rf = grid_search.best_estimator_
y_pred_best = best_rf.predict(X_test)
print("Tuned Model Classification Report:\n", classification_report(y_test, y_pred_best))
print("Tuned Model Confusion Matrix:\n", confusion_matrix(y_test, y_pred_best))
print("Tuned Model ROC AUC Score:", roc_auc_score(y_test, best_rf.predict_proba(X_test)[:, 1]))

# 8. Feature Importance Analysis
importances = best_rf.feature_importances_
features = X.columns
feature_importances = pd.Series(importances, index=features).sort_values(ascending=False)

plt.figure(figsize=(10, 6))
sns.barplot(x=feature_importances, y=feature_importances.index)
plt.xlabel('Importance Score')
plt.ylabel('Features')
plt.title('Feature Importance from Random Forest')
plt.show()
