# OpenShift Webhook Integration

This document describes how to set up automatic deployments using OpenShift webhooks in addition to the GitHub Actions workflow.

## Overview

While the GitHub Actions workflow provides full CI/CD automation, you can also configure OpenShift to automatically redeploy when new images are available using webhooks and image change triggers.

## Setting up ImageChange Triggers

### 1. Enable Auto-deployment for Existing Deployments

For your existing deployments, enable automatic redeployment when new images are available:

```bash
# For frontend deployment
oc set triggers deploy/fcc-physics-events-frontend --from-image=registry.cern.ch/fcc-physics-events/fcc-physics-events-frontend:latest --containers fcc-physics-events-frontend

# For backend deployment  
oc set triggers deploy/fcc-physics-events-backend --from-image=registry.cern.ch/fcc-physics-events/fcc-physics-events-backend:latest --containers fcc-phsyics-events-backend
```

### 2. Manual YAML Configuration

Alternatively, you can edit the deployment YAML files directly to add ImageChange triggers:

#### Frontend Deployment
Add this annotation to `k8s/frontend-deployment.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  annotations:
    image.openshift.io/triggers: |
      [
        {
          "from": {
            "kind": "ImageStreamTag", 
            "name": "fcc-physics-events-frontend:latest"
          },
          "fieldPath": "spec.template.spec.containers[0].image"
        }
      ]
```

#### Backend Deployment  
Add this annotation to `k8s/backend-deployment.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  annotations:
    image.openshift.io/triggers: |
      [
        {
          "from": {
            "kind": "ImageStreamTag",
            "name": "fcc-physics-events-backend:latest" 
          },
          "fieldPath": "spec.template.spec.containers[0].image"
        }
      ]
```

## Setting up GitHub Webhooks for BuildConfigs

If you want to use OpenShift BuildConfigs with GitHub webhooks (alternative to the GitHub Actions approach):

### 1. Create BuildConfigs

Create BuildConfigs for your images:

```bash
# Frontend BuildConfig
oc new-build --name=fcc-physics-events-frontend \
  --docker-image=node:22-alpine3.22 \
  --source=https://github.com/your-username/fcc-physics-events.git \
  --context-dir=frontend \
  --strategy=docker

# Backend BuildConfig  
oc new-build --name=fcc-physics-events-backend \
  --docker-image=python:3.12.11-alpine3.22 \
  --source=https://github.com/your-username/fcc-physics-events.git \
  --context-dir=backend \
  --strategy=docker
```

### 2. Get Webhook URLs

Get the GitHub webhook URLs from your BuildConfigs:

```bash
# For frontend
oc describe bc/fcc-physics-events-frontend | grep -A 5 "GitHub webhook"

# For backend
oc describe bc/fcc-physics-events-backend | grep -A 5 "GitHub webhook"
```

### 3. Configure GitHub Webhooks

1. Go to your GitHub repository
2. Navigate to **Settings** → **Webhooks**
3. Click **Add webhook**
4. Paste the webhook URL from OpenShift
5. Set Content type to **application/json**
6. Leave Secret empty (it's included in the URL)
7. Select **Just the push event**
8. Click **Add webhook**

## Hybrid Approach (Recommended)

The recommended approach is to use both:

1. **GitHub Actions** for complete CI/CD pipeline (build, test, deploy)
2. **ImageChange triggers** for automatic redeployment when images are updated

This provides:
- Full control over the build and deployment process
- Automatic redeployment when images change
- Rollback capabilities
- Build caching and optimization
- Security scanning integration (can be added to GitHub Actions)

## Testing the Setup

### Test ImageChange Triggers

1. Push a new image manually:
   ```bash
   docker build -t registry.cern.ch/fcc-physics-events/fcc-physics-events-frontend:latest ./frontend/
   docker push registry.cern.ch/fcc-physics-events/fcc-physics-events-frontend:latest
   ```

2. Watch for automatic deployment:
   ```bash
   oc get pods -w
   ```

### Test GitHub Webhooks (if using BuildConfigs)

1. Make a code change and push to master
2. Check BuildConfig status:
   ```bash
   oc get builds
   oc logs -f bc/fcc-physics-events-frontend
   ```

## Troubleshooting

### ImageChange Triggers Not Working

1. Check if triggers are properly configured:
   ```bash
   oc describe deploy/fcc-physics-events-frontend | grep -A 10 "Triggers"
   ```

2. Verify ImageStream exists:
   ```bash
   oc get imagestreams
   ```

3. Check deployment events:
   ```bash
   oc get events --sort-by='.lastTimestamp'
   ```

### Webhook Issues

1. Check webhook delivery in GitHub repository settings
2. Verify BuildConfig webhook URL is correct
3. Check OpenShift build logs for errors

## Security Considerations

- Use service accounts with minimal required permissions
- Regularly rotate webhook URLs if compromised
- Monitor build and deployment logs for suspicious activity
- Use signed commits for additional security
