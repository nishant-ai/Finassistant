# Frontend Deployment Guide (S3 + CloudFront)

This guide covers deploying the Financial Assistant React frontend to AWS S3 with CloudFront CDN.

## Important Note

**Frontend is deployed as static files to S3, NOT as a Docker container.**

The `docker-compose.frontend.yml` file is **only** for local testing before deploying to S3. In production:
- **Frontend**: S3 + CloudFront (static files)
- **Backend**: EC2 with Docker (see [DEPLOYMENT_BACKEND.md](DEPLOYMENT_BACKEND.md))

See [DOCKER_DEPLOYMENT.md](DOCKER_DEPLOYMENT.md) for Docker testing options.

## Prerequisites

- AWS Account with S3 and CloudFront access
- AWS CLI installed and configured
- Domain name (optional, for custom domain)
- Backend API deployed and accessible on EC2

## Architecture Overview

```
Users → CloudFront CDN → S3 Bucket (Static Website) → Backend API (EC2)
```

## Step 1: Prepare Frontend for Deployment

### 1.1 Update API Endpoint

Navigate to your frontend directory and update the API endpoint:

```bash
cd frontend
```

Find the API configuration file (usually in `src/config.js` or similar) and update:

```javascript
// src/config.js or where your API URL is defined
const API_BASE_URL = process.env.VITE_API_URL || 'https://api.your-domain.com';
// OR if you're using nginx proxy
const API_BASE_URL = 'https://your-backend-domain.com';

export default {
  apiUrl: API_BASE_URL,
  wsUrl: API_BASE_URL.replace('https', 'wss').replace('http', 'ws') + '/ws/chat'
};
```

### 1.2 Create Environment File

Create `.env.production`:
```bash
nano .env.production
```

Add:
```env
VITE_API_URL=https://your-backend-domain.com
```

### 1.3 Build Production Bundle

```bash
# Install dependencies
npm install

# Build for production
npm run build
```

This creates an optimized build in the `dist/` directory.

### 1.4 Test Build Locally

```bash
npm run preview
```

Visit `http://localhost:4173` to verify the build works.

## Step 2: Setup S3 Bucket

### 2.1 Create S3 Bucket

```bash
# Replace with your bucket name
BUCKET_NAME="finassistant-frontend"
REGION="us-east-1"

# Create bucket
aws s3 mb s3://$BUCKET_NAME --region $REGION
```

### 2.2 Configure Bucket for Static Website Hosting

```bash
# Enable static website hosting
aws s3 website s3://$BUCKET_NAME --index-document index.html --error-document index.html
```

**Note**: We use `index.html` for error document to support React Router.

### 2.3 Create Bucket Policy

Create a file `bucket-policy.json`:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "PublicReadGetObject",
      "Effect": "Allow",
      "Principal": "*",
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::finassistant-frontend/*"
    }
  ]
}
```

**Replace** `finassistant-frontend` with your actual bucket name.

Apply the policy:
```bash
aws s3api put-bucket-policy --bucket $BUCKET_NAME --policy file://bucket-policy.json
```

### 2.4 Disable Block Public Access (for static website)

```bash
aws s3api put-public-access-block \
    --bucket $BUCKET_NAME \
    --public-access-block-configuration \
    "BlockPublicAcls=false,IgnorePublicAcls=false,BlockPublicPolicy=false,RestrictPublicBuckets=false"
```

## Step 3: Upload Frontend to S3

### 3.1 Upload Build Files

From your frontend directory:

```bash
# Upload all files from dist/
aws s3 sync dist/ s3://$BUCKET_NAME --delete

# Set proper content types and cache headers
aws s3 sync dist/ s3://$BUCKET_NAME \
  --delete \
  --cache-control "public, max-age=31536000" \
  --exclude "index.html" \
  --exclude "*.json"

# Upload index.html with no cache (for updates)
aws s3 cp dist/index.html s3://$BUCKET_NAME/index.html \
  --cache-control "no-cache, no-store, must-revalidate" \
  --content-type "text/html"
```

### 3.2 Verify S3 Website

Get the S3 website endpoint:
```bash
echo "http://$BUCKET_NAME.s3-website-$REGION.amazonaws.com"
```

Visit this URL to test your site.

## Step 4: Setup CloudFront Distribution

### 4.1 Create CloudFront Distribution

Create `cloudfront-config.json`:

```json
{
  "CallerReference": "finassistant-frontend-1",
  "Comment": "Financial Assistant Frontend CDN",
  "DefaultRootObject": "index.html",
  "Origins": {
    "Quantity": 1,
    "Items": [
      {
        "Id": "S3-finassistant-frontend",
        "DomainName": "finassistant-frontend.s3.amazonaws.com",
        "S3OriginConfig": {
          "OriginAccessIdentity": ""
        }
      }
    ]
  },
  "DefaultCacheBehavior": {
    "TargetOriginId": "S3-finassistant-frontend",
    "ViewerProtocolPolicy": "redirect-to-https",
    "AllowedMethods": {
      "Quantity": 2,
      "Items": ["GET", "HEAD"],
      "CachedMethods": {
        "Quantity": 2,
        "Items": ["GET", "HEAD"]
      }
    },
    "Compress": true,
    "ForwardedValues": {
      "QueryString": false,
      "Cookies": {
        "Forward": "none"
      }
    },
    "MinTTL": 0,
    "DefaultTTL": 86400,
    "MaxTTL": 31536000
  },
  "CustomErrorResponses": {
    "Quantity": 1,
    "Items": [
      {
        "ErrorCode": 404,
        "ResponsePagePath": "/index.html",
        "ResponseCode": "200",
        "ErrorCachingMinTTL": 300
      }
    ]
  },
  "Enabled": true,
  "PriceClass": "PriceClass_100"
}
```

**Or create via AWS Console** (Recommended for first-time setup):

1. Go to CloudFront Console
2. Click "Create Distribution"
3. Configure:
   - **Origin Domain**: Select your S3 bucket
   - **Origin Access**: Legacy access identities (create new OAI)
   - **Viewer Protocol Policy**: Redirect HTTP to HTTPS
   - **Allowed HTTP Methods**: GET, HEAD
   - **Compress Objects**: Yes
   - **Price Class**: Use all edge locations (or select based on needs)
   - **Alternate Domain Names (CNAMEs)**: Your custom domain (if any)
   - **SSL Certificate**: Request or import certificate via ACM
   - **Default Root Object**: `index.html`

4. Click "Create Distribution"

### 4.2 Configure Custom Error Pages

In CloudFront distribution settings:

1. Go to "Error Pages" tab
2. Create custom error response:
   - **HTTP Error Code**: 404
   - **Customize Error Response**: Yes
   - **Response Page Path**: `/index.html`
   - **HTTP Response Code**: 200

This ensures React Router works properly.

### 4.3 Update S3 Bucket Policy for CloudFront OAI

After creating OAI in CloudFront, update your S3 bucket policy:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowCloudFrontOAI",
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::cloudfront:user/CloudFront Origin Access Identity YOUR_OAI_ID"
      },
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::finassistant-frontend/*"
    }
  ]
}
```

Apply:
```bash
aws s3api put-bucket-policy --bucket $BUCKET_NAME --policy file://updated-bucket-policy.json
```

### 4.4 Get CloudFront Domain

```bash
# List distributions
aws cloudfront list-distributions --query 'DistributionList.Items[*].[Id,DomainName]' --output table
```

Note your CloudFront domain: `d1234abcd.cloudfront.net`

## Step 5: Setup Custom Domain (Optional)

### 5.1 Request SSL Certificate in ACM

**Important**: Certificate must be in `us-east-1` region for CloudFront.

```bash
# Request certificate
aws acm request-certificate \
  --domain-name your-domain.com \
  --subject-alternative-names www.your-domain.com \
  --validation-method DNS \
  --region us-east-1
```

### 5.2 Validate Certificate

1. Go to ACM Console in `us-east-1`
2. Click on the certificate
3. Create the CNAME records in your DNS provider
4. Wait for validation (can take 5-30 minutes)

### 5.3 Add Custom Domain to CloudFront

1. Go to CloudFront distribution
2. Click "Edit"
3. Add **Alternate Domain Names (CNAMEs)**: `your-domain.com, www.your-domain.com`
4. Select your **SSL Certificate** from ACM
5. Save changes

### 5.4 Update DNS Records

In your DNS provider (Route53, Cloudflare, etc.):

**For Route53**:
```bash
# Create A record (Alias) pointing to CloudFront
# Use AWS Console or CLI to create Alias record
```

**For other DNS providers**:
Create CNAME records:
```
your-domain.com    → d1234abcd.cloudfront.net
www.your-domain.com → d1234abcd.cloudfront.net
```

## Step 6: Deployment Script

Create `deploy.sh` in the frontend directory:

```bash
#!/bin/bash

# Configuration
BUCKET_NAME="finassistant-frontend"
DISTRIBUTION_ID="YOUR_CLOUDFRONT_DISTRIBUTION_ID"
REGION="us-east-1"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}Starting deployment...${NC}"

# Build
echo -e "${BLUE}Building production bundle...${NC}"
npm run build

if [ $? -ne 0 ]; then
    echo "Build failed!"
    exit 1
fi

# Upload to S3
echo -e "${BLUE}Uploading to S3...${NC}"
aws s3 sync dist/ s3://$BUCKET_NAME \
  --delete \
  --cache-control "public, max-age=31536000" \
  --exclude "index.html" \
  --exclude "*.json"

aws s3 cp dist/index.html s3://$BUCKET_NAME/index.html \
  --cache-control "no-cache, no-store, must-revalidate" \
  --content-type "text/html"

# Invalidate CloudFront cache
echo -e "${BLUE}Invalidating CloudFront cache...${NC}"
aws cloudfront create-invalidation \
  --distribution-id $DISTRIBUTION_ID \
  --paths "/*"

echo -e "${GREEN}Deployment complete!${NC}"
echo -e "Site URL: https://your-domain.com"
```

Make it executable:
```bash
chmod +x deploy.sh
```

Usage:
```bash
./deploy.sh
```

## Step 7: Update Backend CORS

Update your backend [api/app.py:54-60](api/app.py#L54-L60) to allow your frontend domain:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://your-domain.com",
        "https://www.your-domain.com",
        "https://d1234abcd.cloudfront.net"  # CloudFront domain
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

Rebuild and redeploy your backend:
```bash
# On EC2
cd ~/Finassistant
git pull
docker-compose build
docker-compose up -d
```

## Step 8: CI/CD with GitHub Actions (Optional)

Create `.github/workflows/deploy-frontend.yml`:

```yaml
name: Deploy Frontend to S3

on:
  push:
    branches: [ main ]
    paths:
      - 'frontend/**'

jobs:
  deploy:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v3

    - name: Setup Node.js
      uses: actions/setup-node@v3
      with:
        node-version: '18'

    - name: Install dependencies
      working-directory: ./frontend
      run: npm ci

    - name: Build
      working-directory: ./frontend
      env:
        VITE_API_URL: ${{ secrets.VITE_API_URL }}
      run: npm run build

    - name: Configure AWS credentials
      uses: aws-actions/configure-aws-credentials@v2
      with:
        aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
        aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
        aws-region: us-east-1

    - name: Deploy to S3
      working-directory: ./frontend
      run: |
        aws s3 sync dist/ s3://${{ secrets.S3_BUCKET }} \
          --delete \
          --cache-control "public, max-age=31536000" \
          --exclude "index.html"
        aws s3 cp dist/index.html s3://${{ secrets.S3_BUCKET }}/index.html \
          --cache-control "no-cache"

    - name: Invalidate CloudFront
      run: |
        aws cloudfront create-invalidation \
          --distribution-id ${{ secrets.CLOUDFRONT_DISTRIBUTION_ID }} \
          --paths "/*"
```

Add these secrets to GitHub:
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `S3_BUCKET`
- `CLOUDFRONT_DISTRIBUTION_ID`
- `VITE_API_URL`

## Troubleshooting

### Blank Page After Deployment
- Check browser console for errors
- Verify API URL is correct in environment variables
- Check CORS settings on backend
- Ensure CloudFront error pages are configured

### API Calls Failing
- Verify backend CORS allows your frontend domain
- Check API URL in browser network tab
- Ensure SSL certificate is valid
- Test API directly: `curl https://your-backend/api/health`

### CloudFront Shows Old Version
- Create invalidation: `aws cloudfront create-invalidation --distribution-id ID --paths "/*"`
- Wait 5-10 minutes for invalidation to complete
- Clear browser cache (Cmd+Shift+R or Ctrl+Shift+R)

### React Router 404 Errors
- Verify CloudFront custom error page is set to redirect 404 to `/index.html`
- Check S3 website error document is set to `index.html`

## Performance Optimization

### 1. Enable Compression
CloudFront automatically compresses (already enabled if you followed this guide).

### 2. Optimize Images
```bash
# Install image optimization tools
npm install --save-dev vite-plugin-imagemin

# Add to vite.config.js
import viteImagemin from 'vite-plugin-imagemin';

export default defineConfig({
  plugins: [
    react(),
    viteImagemin({
      gifsicle: { optimizationLevel: 7 },
      optipng: { optimizationLevel: 7 },
      mozjpeg: { quality: 80 },
      svgo: { plugins: [{ name: 'removeViewBox' }] }
    })
  ]
});
```

### 3. Code Splitting
Vite does this automatically, but ensure you're using dynamic imports for large components:
```javascript
const HeavyComponent = lazy(() => import('./HeavyComponent'));
```

### 4. Cache Busting
Vite automatically adds hashes to filenames. Our deployment script handles cache headers correctly.

## Cost Estimation

Monthly costs (approximate):
- **S3 Storage**: $0.023/GB (~$0.05 for typical React app)
- **S3 Requests**: $0.005/1000 GET requests
- **CloudFront**: First 1TB transfer free (AWS Free Tier), then $0.085/GB
- **Route53** (if used): $0.50/hosted zone + $0.40/million queries

**Total**: ~$1-5/month for small to medium traffic

## Security Best Practices

### 1. Enable CloudFront Security Headers
Add Lambda@Edge or CloudFront Functions to add security headers:
```javascript
function handler(event) {
    var response = event.response;
    response.headers = {
        ...response.headers,
        'strict-transport-security': { value: 'max-age=63072000; includeSubdomains; preload' },
        'x-content-type-options': { value: 'nosniff' },
        'x-frame-options': { value: 'DENY' },
        'x-xss-protection': { value: '1; mode=block' },
        'referrer-policy': { value: 'same-origin' }
    };
    return response;
}
```

### 2. Use AWS WAF (Optional)
Add Web Application Firewall to CloudFront for DDoS protection and rate limiting.

### 3. Enable CloudFront Logging
```bash
aws cloudfront update-distribution \
  --id YOUR_DISTRIBUTION_ID \
  --logging Bucket=your-logs-bucket.s3.amazonaws.com,Prefix=cloudfront/,Enabled=true
```

## Monitoring

### CloudWatch Metrics
Monitor these CloudFront metrics:
- Requests
- Bytes Downloaded
- Error Rate
- Cache Hit Rate

### Set Up Alarms
```bash
aws cloudwatch put-metric-alarm \
  --alarm-name high-error-rate \
  --alarm-description "Alert when error rate > 5%" \
  --metric-name 4xxErrorRate \
  --namespace AWS/CloudFront \
  --statistic Average \
  --period 300 \
  --evaluation-periods 2 \
  --threshold 5 \
  --comparison-operator GreaterThanThreshold
```

## Next Steps

1. Setup monitoring and alerts
2. Configure AWS WAF for security
3. Implement CloudFront Functions for headers
4. Setup automated backups
5. Configure CI/CD pipeline
6. Test disaster recovery procedures

## Support

For issues:
- Check CloudFront distribution logs
- Verify S3 bucket permissions
- Test API connectivity from frontend
- Review browser console for errors
