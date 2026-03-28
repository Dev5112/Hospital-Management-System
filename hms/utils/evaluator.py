"""
Model evaluation utilities for HMS AI/ML System.
Provides comprehensive evaluation metrics and visualization.
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, confusion_matrix, classification_report,
    mean_absolute_error, mean_squared_error, r2_score
)
import json
from pathlib import Path
from typing import Dict, Any, Optional


def evaluate_classifier(
    model: Any,
    X_test: pd.DataFrame,
    y_test: pd.Series,
    model_name: str,
    output_dir: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Evaluate classification model comprehensively.

    Args:
        model: Trained classifier
        X_test: Test features
        y_test: Test labels
        model_name: Name of model for saving outputs
        output_dir: Directory to save visualizations

    Returns:
        Dictionary with evaluation metrics
    """
    # Make predictions
    y_pred = model.predict(X_test)
    y_pred_proba = model.predict_proba(X_test)

    # Calculate metrics
    accuracy = accuracy_score(y_test, y_pred)
    precision = precision_score(y_test, y_pred, average="weighted", zero_division=0)
    recall = recall_score(y_test, y_pred, average="weighted", zero_division=0)
    f1 = f1_score(y_test, y_pred, average="weighted", zero_division=0)

    # ROC-AUC for binary classification
    try:
        if len(np.unique(y_test)) == 2:
            roc_auc = roc_auc_score(y_test, y_pred_proba[:, 1])
        else:
            roc_auc = roc_auc_score(y_test, y_pred_proba, multi_class="ovr", average="macro")
    except:
        roc_auc = None

    # Confusion matrix
    cm = confusion_matrix(y_test, y_pred)

    # Classification report
    report = classification_report(y_test, y_pred, output_dict=True, zero_division=0)

    results = {
        "model_name": model_name,
        "accuracy": round(accuracy, 4),
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1_score": round(f1, 4),
        "roc_auc": round(roc_auc, 4) if roc_auc is not None else None,
        "num_test_samples": len(y_test),
    }

    # Print report
    print(f"\n{'='*60}")
    print(f"Classification Report: {model_name}")
    print(f"{'='*60}")
    print(f"Accuracy:  {accuracy:.4f}")
    print(f"Precision: {precision:.4f}")
    print(f"Recall:    {recall:.4f}")
    print(f"F1-Score:  {f1:.4f}")
    if roc_auc is not None:
        print(f"ROC-AUC:   {roc_auc:.4f}")
    print(f"\nClassification Report:\n{classification_report(y_test, y_pred, zero_division=0)}")

    # Save confusion matrix visualization
    if output_dir:
        output_dir = Path(output_dir)
        output_dir.mkdir(exist_ok=True)

        plt.figure(figsize=(10, 8))
        sns.heatmap(cm, annot=True, fmt="d", cmap="Blues", cbar=True)
        plt.title(f"Confusion Matrix - {model_name}")
        plt.ylabel("True Label")
        plt.xlabel("Predicted Label")
        plt.tight_layout()
        plt.savefig(output_dir / f"{model_name}_confusion_matrix.png", dpi=100)
        plt.close()

    return results


def evaluate_regressor(
    model: Any,
    X_test: pd.DataFrame,
    y_test: pd.Series,
    model_name: str,
    output_dir: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Evaluate regression model comprehensively.

    Args:
        model: Trained regressor
        X_test: Test features
        y_test: Test labels
        model_name: Name of model for saving outputs
        output_dir: Directory to save visualizations

    Returns:
        Dictionary with evaluation metrics
    """
    # Make predictions
    y_pred = model.predict(X_test)

    # Calculate metrics
    mae = mean_absolute_error(y_test, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    r2 = r2_score(y_test, y_pred)

    results = {
        "model_name": model_name,
        "mae": round(mae, 4),
        "rmse": round(rmse, 4),
        "r2_score": round(r2, 4),
        "num_test_samples": len(y_test),
    }

    # Print report
    print(f"\n{'='*60}")
    print(f"Regression Report: {model_name}")
    print(f"{'='*60}")
    print(f"MAE:  {mae:.4f}")
    print(f"RMSE: {rmse:.4f}")
    print(f"R²:   {r2:.4f}")

    # Save residual plot
    if output_dir:
        output_dir = Path(output_dir)
        output_dir.mkdir(exist_ok=True)

        residuals = y_test - y_pred

        fig, axes = plt.subplots(1, 2, figsize=(14, 5))

        # Residuals vs Predicted
        axes[0].scatter(y_pred, residuals, alpha=0.5)
        axes[0].axhline(y=0, color="r", linestyle="--")
        axes[0].set_xlabel("Predicted Values")
        axes[0].set_ylabel("Residuals")
        axes[0].set_title(f"Residuals Plot - {model_name}")

        # Residuals distribution
        axes[1].hist(residuals, bins=30, edgecolor="black")
        axes[1].set_xlabel("Residuals")
        axes[1].set_ylabel("Frequency")
        axes[1].set_title("Residuals Distribution")

        plt.tight_layout()
        plt.savefig(output_dir / f"{model_name}_residuals.png", dpi=100)
        plt.close()

    return results


def plot_feature_importance(
    model: Any,
    feature_names: list,
    model_name: str,
    top_n: int = 15,
    output_dir: Optional[Path] = None
) -> None:
    """
    Plot feature importance for tree-based models.

    Args:
        model: Trained model with feature_importances_ attribute
        feature_names: List of feature names
        model_name: Name of model
        top_n: Number of top features to display
        output_dir: Directory to save visualization
    """
    if not hasattr(model, "feature_importances_"):
        print(f"Model {model_name} does not have feature_importances_ attribute")
        return

    importances = model.feature_importances_
    indices = np.argsort(importances)[::-1][:top_n]

    plt.figure(figsize=(10, 6))
    plt.title(f"Top {top_n} Feature Importances - {model_name}")
    plt.bar(range(top_n), importances[indices])
    plt.xticks(range(top_n), [feature_names[i] for i in indices], rotation=45, ha="right")
    plt.ylabel("Importance")
    plt.tight_layout()

    if output_dir:
        output_dir = Path(output_dir)
        output_dir.mkdir(exist_ok=True)
        plt.savefig(output_dir / f"{model_name}_feature_importance.png", dpi=100)

    plt.close()


def plot_roc_curve(
    model: Any,
    X_test: pd.DataFrame,
    y_test: pd.Series,
    model_name: str,
    output_dir: Optional[Path] = None
) -> None:
    """
    Plot ROC curve for binary classification.

    Args:
        model: Trained binary classifier
        X_test: Test features
        y_test: Test labels
        model_name: Name of model
        output_dir: Directory to save visualization
    """
    from sklearn.metrics import roc_curve, auc

    try:
        y_pred_proba = model.predict_proba(X_test)[:, 1]
        fpr, tpr, _ = roc_curve(y_test, y_pred_proba)
        roc_auc = auc(fpr, tpr)

        plt.figure(figsize=(8, 6))
        plt.plot(fpr, tpr, color="darkorange", lw=2, label=f"ROC curve (AUC = {roc_auc:.2f})")
        plt.plot([0, 1], [0, 1], color="navy", lw=2, linestyle="--", label="Random Classifier")
        plt.xlim([0.0, 1.0])
        plt.ylim([0.0, 1.05])
        plt.xlabel("False Positive Rate")
        plt.ylabel("True Positive Rate")
        plt.title(f"ROC Curve - {model_name}")
        plt.legend(loc="lower right")
        plt.tight_layout()

        if output_dir:
            output_dir = Path(output_dir)
            output_dir.mkdir(exist_ok=True)
            plt.savefig(output_dir / f"{model_name}_roc_curve.png", dpi=100)

        plt.close()
    except Exception as e:
        print(f"Could not plot ROC curve: {e}")


def plot_learning_curve(
    model: Any,
    X_train: pd.DataFrame,
    y_train: pd.Series,
    X_test: pd.DataFrame,
    y_test: pd.Series,
    model_name: str,
    metric: str = "accuracy",
    output_dir: Optional[Path] = None
) -> None:
    """
    Plot learning curve showing train/test performance.

    Args:
        model: Fitted model
        X_train: Training features
        y_train: Training labels
        X_test: Test features
        y_test: Test labels
        model_name: Name of model
        metric: Metric to plot ("accuracy" or other)
        output_dir: Directory to save visualization
    """
    from sklearn.model_selection import learning_curve

    try:
        train_sizes, train_scores, val_scores = learning_curve(
            model, X_train, y_train, cv=5, n_jobs=-1, scoring=metric
        )

        train_mean = np.mean(train_scores, axis=1)
        train_std = np.std(train_scores, axis=1)
        val_mean = np.mean(val_scores, axis=1)
        val_std = np.std(val_scores, axis=1)

        plt.figure(figsize=(10, 6))
        plt.plot(train_sizes, train_mean, label="Training score", color="blue", marker="o")
        plt.fill_between(train_sizes, train_mean - train_std, train_mean + train_std, alpha=0.2, color="blue")
        plt.plot(train_sizes, val_mean, label="Validation score", color="green", marker="o")
        plt.fill_between(train_sizes, val_mean - val_std, val_mean + val_std, alpha=0.2, color="green")
        plt.xlabel("Training Set Size")
        plt.ylabel(f"{metric.capitalize()}")
        plt.title(f"Learning Curve - {model_name}")
        plt.legend(loc="best")
        plt.grid(True, alpha=0.3)
        plt.tight_layout()

        if output_dir:
            output_dir = Path(output_dir)
            output_dir.mkdir(exist_ok=True)
            plt.savefig(output_dir / f"{model_name}_learning_curve.png", dpi=100)

        plt.close()
    except Exception as e:
        print(f"Could not plot learning curve: {e}")


def save_evaluation_report(results: Dict[str, Any], output_path: Path) -> None:
    """
    Save evaluation results to JSON file.

    Args:
        results: Dictionary with evaluation metrics
        output_path: Path to save JSON file
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w") as f:
        json.dump(results, f, indent=4, default=str)

    print(f"Evaluation report saved to {output_path}")


if __name__ == "__main__":
    """Demo: Test evaluation functions"""
    from sklearn.datasets import make_classification, make_regression
    from sklearn.model_selection import train_test_split
    from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
    import tempfile

    print("Testing evaluation utilities...")

    # Classification demo
    X, y = make_classification(n_samples=200, n_features=20, random_state=42)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    clf = RandomForestClassifier(n_estimators=100, random_state=42)
    clf.fit(X_train, y_train)

    X_test_df = pd.DataFrame(X_test, columns=[f"feature_{i}" for i in range(X.shape[1])])
    y_test_series = pd.Series(y_test)

    print("\nClassification Evaluation:")
    eval_results = evaluate_classifier(clf, X_test_df, y_test_series, "RandomForest_Classifier")

    # Regression demo
    X, y = make_regression(n_samples=200, n_features=20, random_state=42)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    regressor = RandomForestRegressor(n_estimators=100, random_state=42)
    regressor.fit(X_train, y_train)

    X_test_df = pd.DataFrame(X_test, columns=[f"feature_{i}" for i in range(X.shape[1])])
    y_test_series = pd.Series(y_test)

    print("\nRegression Evaluation:")
    eval_results = evaluate_regressor(regressor, X_test_df, y_test_series, "RandomForest_Regressor")
