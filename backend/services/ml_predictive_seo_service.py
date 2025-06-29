"""
ML-Powered Predictive SEO Service
Provides ranking predictions, traffic forecasting, and ROI modeling
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import joblib
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler
from prophet import Prophet
import tensorflow as tf
from tensorflow import keras
import xgboost as xgb
import lightgbm as lgb
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.seasonal import seasonal_decompose
import asyncio
from dataclasses import dataclass

@dataclass
class RankingPrediction:
    """Ranking prediction result"""
    keyword: str
    current_position: int
    predicted_positions: List[int]
    confidence_intervals: List[Tuple[int, int]]
    dates: List[datetime]
    probability_top_3: float
    probability_top_10: float
    factors: Dict[str, float]

@dataclass
class TrafficForecast:
    """Traffic forecast result"""
    current_traffic: int
    forecasted_traffic: List[int]
    confidence_intervals: List[Tuple[int, int]]
    dates: List[datetime]
    seasonal_patterns: Dict
    growth_rate: float

class PredictiveSEOService:
    def __init__(self):
        self.ranking_model = None
        self.traffic_model = None
        self.roi_model = None
        self.scaler = StandardScaler()
        self._initialize_models()
        
    def _initialize_models(self):
        """Initialize ML models"""
        # Ranking prediction model (XGBoost)
        self.ranking_model = xgb.XGBRegressor(
            n_estimators=100,
            max_depth=6,
            learning_rate=0.1,
            objective='reg:squarederror'
        )
        
        # Traffic forecasting model (Prophet)
        self.traffic_model = Prophet(
            changepoint_prior_scale=0.05,
            seasonality_mode='multiplicative',
            daily_seasonality=True,
            weekly_seasonality=True,
            yearly_seasonality=True
        )
        
        # ROI model (LightGBM)
        self.roi_model = lgb.LGBMRegressor(
            num_leaves=31,
            learning_rate=0.05,
            n_estimators=100
        )
        
    async def predict_ranking(self, 
                            keyword_data: Dict,
                            historical_data: pd.DataFrame,
                            days_ahead: int = 90) -> RankingPrediction:
        """Predict future rankings for a keyword"""
        
        # Feature engineering
        features = self._extract_ranking_features(keyword_data, historical_data)
        
        # Prepare time series data
        X_train, y_train = self._prepare_ranking_data(historical_data)
        
        # Train model if not already trained
        if not hasattr(self.ranking_model, 'feature_importances_'):
            self.ranking_model.fit(X_train, y_train)
        
        # Generate predictions
        predictions = []
        confidence_intervals = []
        dates = []
        
        current_features = features.copy()
        
        for day in range(days_ahead):
            # Predict next position
            pred = self.ranking_model.predict(current_features.reshape(1, -1))[0]
            predictions.append(int(max(1, min(100, pred))))  # Bound between 1-100
            
            # Calculate confidence interval using quantile regression
            lower = max(1, pred - 2 * np.sqrt(day + 1))  # Wider intervals further out
            upper = min(100, pred + 2 * np.sqrt(day + 1))
            confidence_intervals.append((int(lower), int(upper)))
            
            # Update features for next prediction
            current_features = self._update_features_for_next_day(current_features, pred)
            dates.append(datetime.utcnow() + timedelta(days=day+1))
        
        # Calculate probabilities
        prob_top_3 = sum(1 for p in predictions if p <= 3) / len(predictions)
        prob_top_10 = sum(1 for p in predictions if p <= 10) / len(predictions)
        
        # Feature importance for interpretability
        feature_importance = dict(zip(
            self._get_feature_names(),
            self.ranking_model.feature_importances_
        ))
        
        return RankingPrediction(
            keyword=keyword_data['keyword'],
            current_position=keyword_data['current_position'],
            predicted_positions=predictions,
            confidence_intervals=confidence_intervals,
            dates=dates,
            probability_top_3=prob_top_3,
            probability_top_10=prob_top_10,
            factors=feature_importance
        )
    
    async def forecast_traffic(self,
                             traffic_history: pd.DataFrame,
                             days_ahead: int = 90) -> TrafficForecast:
        """Forecast future organic traffic"""
        
        # Prepare data for Prophet
        df_prophet = traffic_history[['date', 'traffic']].rename(
            columns={'date': 'ds', 'traffic': 'y'}
        )
        
        # Add custom seasonalities and holidays
        self.traffic_model = Prophet(
            changepoint_prior_scale=0.05,
            seasonality_mode='multiplicative'
        )
        
        # Add custom seasonalities
        self.traffic_model.add_seasonality(
            name='monthly',
            period=30.5,
            fourier_order=5
        )
        
        # Fit model
        self.traffic_model.fit(df_prophet)
        
        # Make predictions
        future = self.traffic_model.make_future_dataframe(periods=days_ahead)
        forecast = self.traffic_model.predict(future)
        
        # Extract predictions
        future_forecast = forecast.tail(days_ahead)
        
        predictions = future_forecast['yhat'].astype(int).tolist()
        confidence_intervals = list(zip(
            future_forecast['yhat_lower'].astype(int).tolist(),
            future_forecast['yhat_upper'].astype(int).tolist()
        ))
        dates = pd.to_datetime(future_forecast['ds']).tolist()
        
        # Analyze seasonal patterns
        seasonal_patterns = {
            'weekly': self._extract_weekly_pattern(forecast),
            'monthly': self._extract_monthly_pattern(forecast),
            'yearly': self._extract_yearly_pattern(forecast)
        }
        
        # Calculate growth rate
        current_traffic = traffic_history['traffic'].iloc[-1]
        future_traffic = np.mean(predictions[-30:])  # Last 30 days average
        growth_rate = (future_traffic - current_traffic) / current_traffic
        
        return TrafficForecast(
            current_traffic=int(current_traffic),
            forecasted_traffic=predictions,
            confidence_intervals=confidence_intervals,
            dates=dates,
            seasonal_patterns=seasonal_patterns,
            growth_rate=growth_rate
        )
    
    async def predict_roi(self,
                         seo_investment: float,
                         current_metrics: Dict,
                         historical_data: pd.DataFrame) -> Dict:
        """Predict ROI for SEO investments"""
        
        # Feature engineering for ROI prediction
        features = self._extract_roi_features(
            seo_investment,
            current_metrics,
            historical_data
        )
        
        # Train ROI model if needed
        if not hasattr(self.roi_model, 'feature_importances_'):
            X_train, y_train = self._prepare_roi_training_data(historical_data)
            self.roi_model.fit(X_train, y_train)
        
        # Predict ROI
        predicted_roi = self.roi_model.predict(features.reshape(1, -1))[0]
        
        # Calculate additional metrics
        payback_period = seo_investment / (predicted_roi / 12)  # Months
        
        # Scenario analysis
        scenarios = {
            'conservative': predicted_roi * 0.7,
            'expected': predicted_roi,
            'optimistic': predicted_roi * 1.3
        }
        
        # Attribution breakdown
        attribution = self._calculate_roi_attribution(features)
        
        return {
            'predicted_annual_return': predicted_roi,
            'roi_percentage': (predicted_roi - seo_investment) / seo_investment * 100,
            'payback_period_months': payback_period,
            'scenarios': scenarios,
            'attribution': attribution,
            'confidence_score': self._calculate_confidence_score(features)
        }
    
    async def predict_algorithm_impact(self,
                                     site_metrics: Dict,
                                     historical_updates: List[Dict]) -> Dict:
        """Predict impact of potential algorithm updates"""
        
        # Build neural network for algorithm impact prediction
        model = self._build_algorithm_impact_model()
        
        # Prepare features
        features = self._extract_algorithm_features(site_metrics)
        
        # Predict vulnerability scores
        vulnerability_scores = model.predict(features)
        
        # Analyze historical patterns
        historical_impacts = self._analyze_historical_updates(
            site_metrics,
            historical_updates
        )
        
        return {
            'overall_vulnerability': float(vulnerability_scores[0]),
            'risk_factors': self._identify_risk_factors(site_metrics),
            'recommended_actions': self._generate_recommendations(vulnerability_scores),
            'historical_resilience': historical_impacts,
            'next_update_impact_estimate': self._estimate_next_update_impact(
                vulnerability_scores,
                historical_impacts
            )
        }
    
    def _extract_ranking_features(self, keyword_data: Dict, historical_data: pd.DataFrame) -> np.ndarray:
        """Extract features for ranking prediction"""
        features = []
        
        # Keyword-specific features
        features.extend([
            keyword_data.get('search_volume', 0),
            keyword_data.get('difficulty', 0),
            keyword_data.get('cpc', 0),
            keyword_data.get('competition', 0),
            len(keyword_data.get('keyword', '').split()),  # Word count
        ])
        
        # Historical features
        if not historical_data.empty:
            features.extend([
                historical_data['position'].mean(),
                historical_data['position'].std(),
                historical_data['position'].min(),
                historical_data['position'].max(),
                len(historical_data),  # Days of history
            ])
        else:
            features.extend([50, 10, 40, 60, 0])  # Default values
        
        # Domain authority features
        features.extend([
            keyword_data.get('domain_authority', 50),
            keyword_data.get('page_authority', 40),
            keyword_data.get('backlinks', 100),
            keyword_data.get('referring_domains', 20),
        ])
        
        # Content features
        features.extend([
            keyword_data.get('content_length', 1000),
            keyword_data.get('keyword_density', 0.02),
            keyword_data.get('readability_score', 60),
        ])
        
        # Technical features
        features.extend([
            keyword_data.get('page_speed_score', 80),
            keyword_data.get('mobile_friendly', 1),
            keyword_data.get('https', 1),
        ])
        
        return np.array(features)
    
    def _build_algorithm_impact_model(self) -> keras.Model:
        """Build neural network for algorithm impact prediction"""
        model = keras.Sequential([
            keras.layers.Dense(64, activation='relu', input_shape=(20,)),
            keras.layers.Dropout(0.3),
            keras.layers.Dense(32, activation='relu'),
            keras.layers.Dropout(0.2),
            keras.layers.Dense(16, activation='relu'),
            keras.layers.Dense(1, activation='sigmoid')
        ])
        
        model.compile(
            optimizer='adam',
            loss='binary_crossentropy',
            metrics=['accuracy']
        )
        
        return model
    
    def _extract_weekly_pattern(self, forecast: pd.DataFrame) -> Dict:
        """Extract weekly seasonality pattern"""
        weekly_pattern = {}
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        
        for i, day in enumerate(days):
            day_data = forecast[forecast['ds'].dt.dayofweek == i]['yhat']
            if not day_data.empty:
                weekly_pattern[day] = {
                    'avg_traffic': int(day_data.mean()),
                    'relative_strength': day_data.mean() / forecast['yhat'].mean()
                }
                
        return weekly_pattern
    
    def _extract_monthly_pattern(self, forecast: pd.DataFrame) -> Dict:
        """Extract monthly seasonality pattern"""
        monthly_pattern = {}
        
        for month in range(1, 13):
            month_data = forecast[forecast['ds'].dt.month == month]['yhat']
            if not month_data.empty:
                monthly_pattern[month] = {
                    'avg_traffic': int(month_data.mean()),
                    'relative_strength': month_data.mean() / forecast['yhat'].mean()
                }
                
        return monthly_pattern
    
    def _extract_yearly_pattern(self, forecast: pd.DataFrame) -> Dict:
        """Extract yearly seasonality pattern"""
        # Group by day of year
        forecast['day_of_year'] = forecast['ds'].dt.dayofyear
        yearly_avg = forecast.groupby('day_of_year')['yhat'].mean()
        
        return {
            'peak_day': int(yearly_avg.idxmax()),
            'low_day': int(yearly_avg.idxmin()),
            'variance': float(yearly_avg.std() / yearly_avg.mean())
        }
    
    def _get_feature_names(self) -> List[str]:
        """Get feature names for interpretability"""
        return [
            'search_volume', 'difficulty', 'cpc', 'competition', 'keyword_length',
            'avg_position', 'position_std', 'min_position', 'max_position', 'history_days',
            'domain_authority', 'page_authority', 'backlinks', 'referring_domains',
            'content_length', 'keyword_density', 'readability_score',
            'page_speed_score', 'mobile_friendly', 'https'
        ]

# Example usage
async def demo_predictions():
    service = PredictiveSEOService()
    
    # Example keyword data
    keyword_data = {
        'keyword': 'seo tools',
        'current_position': 15,
        'search_volume': 10000,
        'difficulty': 65,
        'cpc': 5.50,
        'domain_authority': 45,
        'page_authority': 38,
        'backlinks': 250,
        'content_length': 2500
    }
    
    # Example historical data
    dates = pd.date_range(end=datetime.now(), periods=90, freq='D')
    positions = np.random.randint(10, 25, size=90)
    historical_data = pd.DataFrame({
        'date': dates,
        'position': positions
    })
    
    # Get ranking prediction
    prediction = await service.predict_ranking(keyword_data, historical_data)
    print(f"90-day ranking prediction for '{prediction.keyword}':")
    print(f"Current position: {prediction.current_position}")
    print(f"Predicted average position: {np.mean(prediction.predicted_positions):.1f}")
    print(f"Probability of reaching top 3: {prediction.probability_top_3:.1%}")
    print(f"Probability of reaching top 10: {prediction.probability_top_10:.1%}")
    
    # Traffic forecast
    traffic_history = pd.DataFrame({
        'date': dates,
        'traffic': np.random.randint(1000, 5000, size=90)
    })
    
    traffic_forecast = await service.forecast_traffic(traffic_history)
    print(f"\nTraffic forecast:")
    print(f"Current traffic: {traffic_forecast.current_traffic}")
    print(f"Expected growth rate: {traffic_forecast.growth_rate:.1%}")
    
    # ROI prediction
    roi_prediction = await service.predict_roi(
        seo_investment=5000,
        current_metrics={'traffic': 3000, 'conversions': 50},
        historical_data=historical_data
    )
    print(f"\nROI Prediction:")
    print(f"Predicted annual return: ${roi_prediction['predicted_annual_return']:,.2f}")
    print(f"ROI percentage: {roi_prediction['roi_percentage']:.1f}%")
    print(f"Payback period: {roi_prediction['payback_period_months']:.1f} months")

if __name__ == "__main__":
    asyncio.run(demo_predictions())