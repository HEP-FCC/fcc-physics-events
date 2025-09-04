# GitHub Actions Setup Guide

This guide will help you set up GitHub Actions for automated deployment of the FCC Physics Events application to OpenShift.

## Prerequisites

1. **CERN Service Account**: You mentioned you have a CERN service account with access rights to the PaaS OpenShift project.
2. **OpenShift Access**: Ensure your service account has the necessary permissions to deploy to your OpenShift namespace.
3. **Container Registry Access**: Ensure your service account can push to `registry.cern.ch/fcc-physics-events/`.

## Required GitHub Secrets

You need to configure the following secrets in your GitHub repository. Go to **Settings** → **Secrets and variables** → **Actions** → **New repository secret**.

### 1. Container Registry Credentials
- **`CERN_REGISTRY_USER`**: Your CERN registry username (your service account username)
- **`CERN_REGISTRY_PASSWORD`**: Your CERN registry password (your service account password or token)

### 2. OpenShift Credentials
- **`OPENSHIFT_SERVER`**: Your OpenShift server URL
  - Format: `https://openshift.cern.ch` (or your specific server URL)
  - To find this: Run `oc whoami --show-server` if you have oc CLI configured locally
- **`OPENSHIFT_TOKEN`**: Your service account token for OpenShift authentication
  - This should be a long-lived service account token
  - Format: `sha256~...` (long alphanumeric string)
- **`OPENSHIFT_NAMESPACE`**: Your OpenShift project/namespace name
  - This is the name of your OpenShift project where the application is deployed

## How to Obtain OpenShift Credentials

### Option 1: Using Service Account Token (Recommended)
1. Log into OpenShift web console
2. Navigate to your project
3. Go to **Workloads** → **Secrets**
4. Look for service account tokens or create a new service account
5. Copy the token value

### Option 2: Using Personal Token
1. Log into OpenShift web console
2. Click your username in the top right
3. Click **Copy login command**
4. Click **Display Token**
5. Copy the token from the `--token=` parameter

### Option 3: Using CLI
If you're already logged in via CLI:
```bash
oc whoami --show-token
oc whoami --show-server
```

## GitHub Secrets Configuration

### Step-by-step process:

1. **Go to your GitHub repository**
2. **Click on "Settings" tab**
3. **In the left sidebar, click "Secrets and variables" → "Actions"**
4. **Click "New repository secret"**
5. **Add each secret one by one:**

   ```
   Name: CERN_REGISTRY_USER
   Secret: [your-service-account-username]
   ```

   ```
   Name: CERN_REGISTRY_PASSWORD
   Secret: [your-service-account-password]
   ```

   ```
   Name: OPENSHIFT_SERVER
   Secret: https://openshift.cern.ch
   ```

   ```
   Name: OPENSHIFT_TOKEN
   Secret: sha256~[your-long-token-string]
   ```

   ```
   Name: OPENSHIFT_NAMESPACE
   Secret: [your-project-namespace]
   ```

## Workflow Features

The GitHub Actions workflow (`deploy.yml`) includes:

### **Smart Change Detection**
- Only builds frontend image when frontend code changes
- Only builds backend image when backend code changes
- Only deploys when there are relevant changes

### **Efficient Docker Builds**
- Uses Docker BuildKit for faster builds
- Implements GitHub Actions cache for Docker layers
- Builds multi-stage Docker images efficiently

### **Secure Authentication**
- Uses secure token-based authentication for OpenShift
- Stores all credentials in GitHub Secrets
- Uses official RedHat OpenShift actions

### **Deployment Verification**
- Waits for deployments to be ready
- Verifies deployment status
- Provides detailed logging

## Testing the Setup

### 1. Test with a Small Change
Make a small change to your code and push to the `master` branch:
```bash
git checkout master
echo "# Test change" >> README.md
git add README.md
git commit -m "test: trigger GitHub Actions"
git push origin master
```

### 2. Monitor the Workflow
1. Go to your GitHub repository
2. Click on the "Actions" tab
3. Watch the workflow execution
4. Check each job's logs for any issues

### 3. Verify Deployment
After successful workflow execution:
1. Check your OpenShift console
2. Verify pods are running
3. Test application functionality

## Troubleshooting

### Common Issues and Solutions

#### 1. **Authentication Failed**
- **Error**: `Error from server (Unauthorized): ...`
- **Solution**: Verify your `OPENSHIFT_TOKEN` and `OPENSHIFT_SERVER` are correct

#### 2. **Registry Push Failed**
- **Error**: `denied: requested access to the resource is denied`
- **Solution**: Verify your `CERN_REGISTRY_USER` and `CERN_REGISTRY_PASSWORD` are correct

#### 3. **Namespace Not Found**
- **Error**: `Error from server (Forbidden): namespaces ... is forbidden`
- **Solution**: Verify your `OPENSHIFT_NAMESPACE` is correct and your service account has access

#### 4. **Deployment Timeout**
- **Error**: `error: timed out waiting for the condition`
- **Solution**: Check OpenShift console for pod status and logs

### Debug Commands
Add these steps to your workflow for debugging if needed:

```yaml
- name: Debug OpenShift Connection
  run: |
    oc whoami
    oc get pods
    oc describe nodes
```

## Security Considerations

1. **Service Account Permissions**: Ensure your service account has minimal required permissions
2. **Token Rotation**: Regularly rotate your service account tokens
3. **Secret Access**: Limit repository access to trusted collaborators
4. **Audit Logs**: Monitor OpenShift audit logs for deployment activities

## Manual Deployment Fallback

If GitHub Actions fails, you can still deploy manually:

```bash
# Build images locally
docker build -t registry.cern.ch/fcc-physics-events/fcc-physics-events-frontend:latest ./frontend/
docker build -t registry.cern.ch/fcc-physics-events/fcc-physics-events-backend:latest ./backend/

# Push images
docker push registry.cern.ch/fcc-physics-events/fcc-physics-events-frontend:latest
docker push registry.cern.ch/fcc-physics-events/fcc-physics-events-backend:latest

# Deploy to OpenShift
oc login --server=https://openshift.cern.ch --token=your-token
oc project your-namespace
oc apply -R -f k8s/
```

## Next Steps

1. **Set up GitHub Secrets** as described above
2. **Test the workflow** with a small change
3. **Monitor the first few deployments** to ensure everything works correctly
4. **Set up branch protection rules** (optional) to require successful CI before merging
5. **Configure notifications** (optional) for deployment status

## Support

If you encounter issues:
1. Check the GitHub Actions logs for detailed error messages
2. Verify all secrets are correctly configured
3. Test manual deployment to isolate the issue
4. Check OpenShift console for application status
