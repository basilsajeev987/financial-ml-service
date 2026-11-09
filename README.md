Financial ML Prediction Service
A containerised Financial ML inference API built with FastAPI,
XGBoost, Docker, GitHub Actions, Amazon ECR, AWS
EC2, and Nginx.
Project status: Core API deployment is working on AWS EC2. The
service is publicly reachable over HTTP at the current EC2 public IP.
HTTPS, API authentication, rate limiting, monitoring, and automatic
EC2 deployment are still pending.

Financial disclaimer: This is an experimental demonstration
project, not a validated trading strategy or financial advice. Its
prediction endpoint currently accepts engineered features supplied by
the caller; it does not fetch live market data or generate features
from a live feed.

1. Project overview
The project trains an XGBoost model to classify the next executable
BTC-USD hourly direction and serves predictions through a REST API.

The model was trained using historical Yahoo Finance BTC-USD hourly
data. The deployed API loads the saved model pipeline and validates the
26 expected numerical features before inference.
Current capabilities
- Load the trained XGBoost pipeline at application startup.
- Expose health and model metadata endpoints.
- Accept a ticker and 26 engineered numerical features.
- Validate missing, extra, and non-finite feature values.
- Return an UP/DOWN classification and class probabilities.
- Run as a non-root user inside Docker.
- Build and test through GitHub Actions.
- Push immutable commit-SHA-tagged Docker images to Amazon ECR.
- Run the container on AWS EC2 behind an Nginx reverse proxy.
2. Architecture
Developer
   |
   | git push
   v
GitHub repository
   |
   v
GitHub Actions
   |-- Run API tests
   |-- Build Docker image
   |-- Authenticate to AWS using GitHub OIDC
   |-- Push image to Amazon ECR
   |
   v
Amazon ECR (private repository)
   |
   | EC2 instance role: pull image
   v
AWS EC2 (Ubuntu 24.04, eu-west-2)
   |
   | Nginx :80
   v
FastAPI Docker container
   |
   v
XGBoost model pipeline
AWS deployment details
  Item                                Current value
  AWS region                          eu-west-2 (London)

  EC2 instance ID                     i-0721583cbeeb69672

  EC2 public IPv4                     52.56.72.179 (may change if not using an Elastic IP)

  Operating system                    Ubuntu 24.04 LTS

  Docker                              Installed and running

  Reverse proxy                       Nginx

  API container port                  8000, bound to EC2 localhost only

  Public web port                     80

  ECR repository                      financial-ml-service

  ECR registry                        958986708534.dkr.ecr.eu-west-2.amazonaws.com
GitHub repository                   https://github.com/basilsajeev987/financial-ml-service
Do not publish AWS credentials, GitHub tokens, private keys, or other
secrets in this repository or README.
3. Technology stack
- Language: Python 3.10
- API: FastAPI, Uvicorn, Pydantic
- ML: XGBoost, scikit-learn, NumPy, Pandas, joblib
- Testing: pytest, FastAPI TestClient, httpx
- Containerisation: Docker
- CI: GitHub Actions
- Container registry: Amazon ECR
- Compute: Amazon EC2 (Ubuntu 24.04)
- IAM authentication: GitHub OIDC for CI; EC2 instance role for
  image pulls
- Reverse proxy: Nginx
Python dependencies
The service currently pins:
fastapi==0.115.12
uvicorn[standard]==0.34.0
pydantic==2.10.6
numpy==1.26.4
pandas==2.2.3
scikit-learn==1.7.2
xgboost==3.2.0
joblib==1.2.0
Model compatibility note: The model was exported from a separate
training environment. Confirm that the scikit-learn and XGBoost versions
used during training are compatible with the pinned runtime versions.
Loading serialized scikit-learn objects across versions is not
guaranteed.
4. Repository structure
financial-ml-service/
├── app/
│   ├── __init__.py
│   └── main.py
├── models/
│   ├── ai_model.pkl
│   ├── feature_columns.json
│   └── model_metadata.json
├── tests/
│   └── test_api.py
├── .github/
│   └── workflows/
│       └── deploy.yml
├── requirements.txt
├── Dockerfile
├── .dockerignore
└── .gitignore
The model artifacts are required by the service and are copied into the
Docker image.
5. Model and feature information
Model metadata reported by the deployed API
  Property            Value
  Model name          Financial ML Prediction Service
Model type          Pipeline
Algorithm           XGBoost
Version             1.0.0
Ticker              BTC-USD
Prediction target   next_executable_hour_direction
Feature count       26
Metadata status     demonstration
Expected features
The prediction endpoint expects these 26 features:
return_1
return_3
return_6
return_12
return_24
ema12_distance
ema26_distance
ema50_distance
ema_spread
rsi_14
macd
macd_signal
macd_histogram
bb_position
bb_width
volatility_24
volatility_72
atr_pct
candle_range
candle_body
volume_change
volume_zscore
hour_sin
hour_cos
day_sin
day_cos
Model performance context
The recorded experimental results during development were modest
(approximately 0.53--0.56 validation ROC AUC in earlier experiments).
These results do not establish predictive or trading profitability.
Re-evaluate the model using a robust, leakage-aware out-of-sample
process before any real financial use.
6. API endpoints
The API is served by FastAPI.

  Method   Endpoint        Purpose
  GET    /             Service root/status information
GET    /health       Health check and model-loaded status
GET    /model/info   Model metadata and expected feature names
POST   /predict      Generate a model prediction

Interactive Swagger documentation is available at /docs.
Example health response
{
  "status": "healthy",
  "model_loaded": true
}
Example model information response
{
  "model_type": "Pipeline",
  "model_name": "Financial ML Prediction Service",
  "model_version": "1.0.0",
  "features_count": 26,
  "metadata": {
    "model_name": "Financial ML Prediction Service",
    "algorithm": "XGBoost",
    "ticker": "BTC-USD",
    "prediction_type": "next_executable_hour_direction",
    "features": 26,
    "artifact": "ai_model.pkl",
    "model_status": "demonstration",
    "not_financial_advice": true
  }
}
Example prediction request
Send a JSON object containing ticker and a features object with all
26 expected numeric values.
curl -X POST http://127.0.0.1:8000/predict \
  -H "Content-Type: application/json" \
  -d '{
    "ticker": "BTC-USD",
    "features": {
      "return_1": 0.001,
      "return_3": 0.002,
      "return_6": 0.003,
      "return_12": 0.004,
      "return_24": 0.005,
      "ema12_distance": 0.001,
      "ema26_distance": 0.002,
      "ema50_distance": 0.003,
      "ema_spread": 0.001,
      "rsi_14": 55,
      "macd": 0.5,
      "macd_signal": 0.4,
      "macd_histogram": 0.1,
      "bb_position": 0.6,
      "bb_width": 0.02,
      "volatility_24": 0.01,
      "volatility_72": 0.015,
      "atr_pct": 0.02,
      "candle_range": 0.01,
      "candle_body": 0.005,
      "volume_change": 0.1,
      "volume_zscore": 0.5,
      "hour_sin": 0.5,
      "hour_cos": 0.866,
      "day_sin": 0.78,
      "day_cos": 0.62
    }
  }'
Example response shape (actual probabilities depend on the supplied
feature values):
{
  "status": "success",
  "ticker": "BTC-USD",
  "prediction": "UP",
  "probability_up": 0.505333,
  "probability_down": 0.494667,
  "model": "Financial ML Prediction Service",
  "model_version": "1.0.0"
}
The values above are an example from a synthetic test request, not a
live-market prediction.
7. Run locally
Prerequisites
- Python 3.10
- Git
- Docker (optional, for container execution)
Install dependencies
git clone https://github.com/basilsajeev987/financial-ml-service.git
cd financial-ml-service

python -m pip install --upgrade pip
pip install -r requirements.txt
pip install pytest httpx
Ensure the three model artifacts exist under models/.
Start the API
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
Open:
- API: http://127.0.0.1:8000
- Health: http://127.0.0.1:8000/health
- Swagger: http://127.0.0.1:8000/docs
- Model info: http://127.0.0.1:8000/model/info
Run tests
python -m pytest tests/ -v
8. Docker
Build the image
docker build -t financial-ml-api:1.0.0 .
Run locally
docker run -d \
  --name financial-ml-container \
  -p 8000:8000 \
  financial-ml-api:1.0.0
Inspect logs and health
docker ps -a
docker logs --tail 100 financial-ml-container
curl http://127.0.0.1:8000/health
The production EC2 deployment binds the container to 127.0.0.1:8000 so
public traffic passes through Nginx rather than reaching Uvicorn
directly.
9. CI and Amazon ECR
The GitHub Actions workflow currently:
1. Runs on pushes and pull requests targeting main.
2. Installs Python dependencies.
3. Runs the pytest suite.
4. On pushes to main, obtains an AWS identity token using GitHub
   OIDC.
5. Assumes the GitHubActions-FinancialML-Deploy IAM role.
6. Logs in to Amazon ECR.
7. Builds and pushes the Docker image tagged with the Git commit SHA.
GitHub repository variables
The workflow uses these GitHub Actions repository variables:
  Variable                            Value
  AWS_REGION                        eu-west-2

  AWS_ROLE_ARN                      arn:aws:iam::958986708534:role/GitHubActions-FinancialML-Deploy
ECR_REPOSITORY                    financial-ml-service
These are configuration variables, not credentials. AWS access keys are
not stored in GitHub; the workflow uses OIDC.

Current limitation: CI builds and pushes the image to ECR, but it
does not yet automatically deploy the new image to EC2. EC2 deployment
has been performed manually so far.
10. AWS EC2 deployment
EC2 and IAM
The EC2 instance uses the FinancialML-EC2-InstanceRole instance role.
Its ECR permissions allow image authentication and pulling from the
financial-ml-service repository. The role also has
AmazonSSMManagedInstanceCore attached for Systems Manager access.

The GitHub Actions role is separate and is used by CI to push images to
ECR.
ECR login on EC2
AWS CLI v2 was installed on the Ubuntu instance. The instance role was
verified with:
aws sts get-caller-identity
Authenticate Docker to ECR:
aws ecr get-login-password --region eu-west-2 \
  | sudo docker login \
    --username AWS \
    --password-stdin 958986708534.dkr.ecr.eu-west-2.amazonaws.com
Pull a published image
Replace <COMMIT_SHA> with the exact tag from a successful GitHub
Actions run:
sudo docker pull \
  958986708534.dkr.ecr.eu-west-2.amazonaws.com/financial-ml-service:<COMMIT_SHA>
Run the API container on EC2
The manually deployed image tag used during the initial deployment was:

226d5978b7a35fd9c8382ba8028f32b9d124a4a0
sudo docker run -d \
  --name financial-ml-api \
  --restart unless-stopped \
  -p 127.0.0.1:8000:8000 \
  958986708534.dkr.ecr.eu-west-2.amazonaws.com/financial-ml-service:226d5978b7a35fd9c8382ba8028f32b9d124a4a0
Verify the container
sudo docker ps
sudo docker logs --tail 100 financial-ml-api
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/model/info
A successful health check returns status: healthy and
model_loaded: true.
11. Nginx reverse proxy
Nginx is installed and enabled on EC2. It listens on port 80 and proxies
requests to the FastAPI container at 127.0.0.1:8000.

Current Nginx site configuration:
server {
    listen 80;
    server_name 52.56.72.179;

    client_max_body_size 10M;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
The site is enabled at:
/etc/nginx/sites-enabled/financial-ml-api
Validate and reload after configuration changes:
sudo nginx -t
sudo systemctl reload nginx
sudo systemctl status nginx --no-pager
Public endpoints
The API was verified through the EC2 public address:
- http://52.56.72.179/health
- http://52.56.72.179/docs
- http://52.56.72.179/model/info
The public IPv4 address may change if the instance is stopped and
started unless an Elastic IP is allocated.
12. Network and security configuration
The EC2 security group has public inbound rules for:

  Type      Port Source
  HTTP        80 0.0.0.0/0
HTTPS      443 0.0.0.0/0

Port 8000 is not publicly exposed; the container is bound to
127.0.0.1:8000. SSH port 22 is not opened publicly; the intended
administration path is AWS Systems Manager Session Manager.

The Ubuntu UFW firewall was reported as inactive. The AWS security group
is therefore an important network access control.

Security status: The API is currently publicly reachable over plain
HTTP. Do not send credentials or sensitive data over this connection.
Before treating the service as production-ready, configure TLS,
authentication, rate limiting, request controls, and monitoring. Swagger
documentation is also publicly accessible at present.
13. Current deployment status
Completed
- [x] Train and export the XGBoost model artifacts.
- [x] Build the FastAPI inference service.
- [x] Implement health, model information, and prediction endpoints.
- [x] Add API tests.
- [x] Build the Docker image.
- [x] Configure GitHub Actions test and build workflow.
- [x] Configure GitHub OIDC trust with AWS IAM.
- [x] Push Docker images to Amazon ECR.
- [x] Create the EC2 instance role and ECR pull permissions.
- [x] Launch Ubuntu EC2 instance.
- [x] Install Docker and AWS CLI v2 on EC2.
- [x] Pull the image from ECR.
- [x] Run and verify the FastAPI container on EC2.
- [x] Install and configure Nginx.
- [x] Verify the API through the public EC2 IP over HTTP.
Pending
- [ ] Configure HTTPS/TLS. No domain name is currently available.
- [ ] Add API authentication and authorization.
- [ ] Add rate limiting and abuse protection.
- [ ] Restrict or protect public API documentation.
- [ ] Configure CloudWatch metrics, logs, and alarms.
- [ ] Implement automatic EC2 deployment after successful ECR push
  using AWS Systems Manager.
- [ ] Add deployment rollback and health verification.
- [ ] Add resource and uptime monitoring.
- [ ] Perform load, latency, and reliability tests.
- [ ] Review model/runtime dependency compatibility.
- [ ] Validate model performance on a robust untouched test set.
- [ ] Add a live market-data ingestion and feature-generation pipeline
  if live-market inference is required.
- [ ] Complete operational and architecture documentation.
14. Operational commands
Check container
sudo docker ps -a
Follow application logs
sudo docker logs -f financial-ml-api
Restart API container
sudo docker restart financial-ml-api
Check Nginx
sudo systemctl status nginx --no-pager
sudo nginx -t
Check local API through Nginx
The Nginx virtual host uses the public IP as its server name, so include
the matching Host header:
curl -H "Host: 52.56.72.179" http://127.0.0.1/health
Check public API
curl http://52.56.72.179/health
15. Disclaimer
This repository demonstrates an end-to-end machine-learning API
deployment workflow. The model output is experimental and must not be
interpreted as investment advice or a recommendation to trade.
Predictions depend on the quality and correctness of the supplied
features. The API does not currently connect to a live market-data
provider.
