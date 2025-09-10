# Exploratory Data Analysis Report for Titanic Dataset

## 1. Executive Summary
Key findings from the analysis of the Titanic dataset (891 rows, 12 columns) include:
- **Data Quality**: Missing values are present in Age (177 missing), Cabin (687 missing), and Embarked (2 missing). Outliers are detected in SibSp (30), Parch (15), Fare (20), and Age (2-7 depending on analysis).
- **Distributions**: Age is approximately normally distributed with a mean of 29.7 years. Fare is highly right-skewed with a mean of $32.20. SibSp and Parch show high skewness and kurtosis, indicating many passengers traveled alone or with few relatives.
- **Relationships**: Strong negative correlation between Pclass and Fare (-0.55), suggesting higher classes paid more. Pclass and Age have a moderate negative correlation (-0.34 to -0.37), indicating younger passengers in lower classes. Survived has a negative correlation with Pclass (-0.34) and positive with Fare (0.26), hinting at survival advantages for higher classes and fares.
- **Categorical Insights**: Most passengers were male (64.8%), embarked from Southampton (72.4%), and were in 3rd class (55.1%).
- **Actionable Insights**: Focus on imputing missing Age values, handling outliers in SibSp, Parch, and Fare, and exploring interactions between Pclass, Sex, and Survived for predictive modeling.

## 2. Data Quality Assessment
- **Missing Values**: 
  - Age: 177 missing (19.9% of data) – consider imputation based on other features.
  - Cabin: 687 missing (77.1%) – high missingness, may need exclusion or careful handling.
  - Embarked: 2 missing (0.2%) – minimal impact, can be imputed with mode.
- **Outliers (using Z-score >3)**: 
  - SibSp: 30 outliers (e.g., values up to 8 siblings/spouses).
  - Parch: 15 outliers (e.g., values up to 6 parents/children).
  - Fare: 20 outliers (e.g., max fare $512.33).
  - Age: 2-7 outliers (inconsistency in reports, but values like 80 years are extreme).
- **Recommendations**: Impute Age using median or predictive methods, consider capping or transforming Fare, SibSp, and Parch to reduce skewness, and exclude or impute Cabin cautiously.

## 3. Distribution Analysis Results
- **Numeric Variables**:
  - Age: Mean 29.7, std 14.5, min 0.42, max 80.0 – roughly normal with slight right skew (skewness ~0.39-0.51).
  - Fare: Mean 32.20, std 49.69, min 0.0, max 512.33 – highly right-skewed (skewness 4.78) with many low fares and few high ones.
  - SibSp: Mean 0.52, std 1.10 – most passengers have 0 siblings/spouses (608 cases), skewness 3.69.
  - Parch: Mean 0.38, std 0.81 – majority have 0 parents/children (678 cases), skewness 2.74.
- **Categorical Variables**:
  - Sex: Male (577, 64.8%), Female (314, 35.2%).
  - Embarked: S (644, 72.4%), C (168, 18.9%), Q (77, 8.7%).
  - Pclass: 3 (491, 55.1%), 1 (216, 24.2%), 2 (184, 20.7%).
- **Visual References**: Histograms and boxplots are available in files such as Age_histogram.png, Fare_boxplot.png, SibSp_histogram.png, Parch_boxplot.png, and categorical_histograms.png.

## 4. Relationship Insights
- **Correlation Highlights (Pearson)**:
  - Pclass and Fare: -0.55 (strong negative) – higher class associated with higher fare.
  - SibSp and Parch: 0.41 (moderate positive) – passengers with siblings/spouses tend to have more parents/children.
  - Pclass and Age: -0.34 to -0.37 (moderate negative) – lower classes have younger passengers.
  - Survived and Pclass: -0.34 (moderate negative) – lower survival in lower classes.
  - Survived and Fare: 0.26 (weak positive) – higher fare linked to better survival.
- **Segmentation Analysis**: Boxplots (e.g., boxplot_age_by_sex_pclass.png) show Age distributions vary by Sex and Pclass, with potential interactions affecting survival (referenced in scatter plots like scatter_age_vs_survived_by_pclass.png).
- **Heatmap**: correlation_heatmap.png visualizes these relationships, emphasizing the inverse relationship between Pclass and economic indicators.

## 5. Figure References
- age_plots.png
- Fare_histogram.png
- Fare_boxplot.png
- Age_histogram.png
- Age_boxplot.png
- SibSp_histogram.png
- SibSp_boxplot.png
- Parch_histogram.png
- Parch_boxplot.png
- categorical_histograms.png
- scatter_pclass_fare.png
- scatter_pclass_age.png
- heatmap_correlation.png
- boxplot_age_by_sex_pclass.png
- scatter_age_vs_survived_by_pclass.png
- scatter_age_vs_survived_by_sex.png

## 6. Next Questions for Further Analysis
1. How can we impute missing Age values effectively using other variables like Pclass, Sex, or SibSp?
2. What is the impact of outliers in SibSp, Parch, and Fare on predictive models, and should they be capped or transformed?
3. Are there interaction effects between Sex, Pclass, and Survived that could improve model accuracy?
4. How does the high missingness in Cabin affect analysis, and can it be used as a feature after imputation or encoding?
5. What additional features (e.g., family size from SibSp and Parch) could be engineered to enhance predictions?