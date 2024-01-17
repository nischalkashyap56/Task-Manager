import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error
from sklearn.preprocessing import MinMaxScaler

# Read the DataFrame from a CSV file
df = pd.read_csv('/Users/nischalkashyap/Desktop/taskmanager/datasets/sentiment.csv')  # replace 'your_dataset.csv' with your actual CSV file name

# Assume the DataFrame has columns: feature1, feature2, feature3, feature4, target
features = df[['NPS', 'JSI', 'AR', 'EPR']].values
target = df['Sentiment'].values

# Normalize features
scaler = MinMaxScaler()
features_normalized = scaler.fit_transform(features)

# Split the data into training and testing sets
X_train, X_test, y_train, y_test = train_test_split(features_normalized, target, test_size=0.2, random_state=42)

# Create and train the linear regression model
model = LinearRegression()
model.fit(X_train, y_train)

# Make predictions on the test set
predictions = model.predict(X_test)

# Evaluate the model
mse = mean_squared_error(y_test, predictions)
print(f'Mean Squared Error: {mse}')
print((1-mse)*100)

# Print the coefficients
print('Coefficients:', model.coef_)
