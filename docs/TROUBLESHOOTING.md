# Troubleshooting Guide

## AWS Credentials Issues

### Problem: "ExpiredToken" Error

**Symptom:**
```
An error occurred (ExpiredToken) when calling the GetCallerIdentity operation: 
The security token included in the request is expired
```

**Cause:** You're using temporary credentials (session token) that have expired.

**Solutions:**

#### Option 1: Use IAM User Credentials (Recommended for Development)

1. Go to AWS Console → IAM → Users
2. Select your user → Security Credentials
3. Create Access Key
4. Run the setup script:
   ```bash
   ./setup_aws_credentials.sh
   ```
5. Choose option 1 (IAM User)
6. Enter your Access Key ID and Secret Access Key

#### Option 2: Refresh Temporary Credentials

If using AWS SSO or temporary credentials:

1. Get fresh credentials from your SSO portal or AWS Academy
2. Run the setup script:
   ```bash
   ./setup_aws_credentials.sh
   ```
3. Choose option 2 (Temporary Credentials)
4. Enter all three values (Access Key, Secret Key, Session Token)

#### Option 3: Manual Configuration

Edit `~/.aws/credentials`:
```ini
[default]
aws_access_key_id = YOUR_ACCESS_KEY
aws_secret_access_key = YOUR_SECRET_KEY
# Only include session_token if using temporary credentials
aws_session_token = YOUR_SESSION_TOKEN
```

Edit `~/.aws/config`:
```ini
[default]
region = us-east-1
output = json
```

### Problem: "Unable to parse config file"

**Symptom:**
```
Unable to parse config file: /Users/username/.aws/credentials
```

**Cause:** Credentials file is not in proper INI format.

**Solution:**
```bash
# Run the setup script to fix formatting
./setup_aws_credentials.sh
```

Or manually ensure the file has this format:
```ini
[default]
aws_access_key_id = YOUR_KEY
aws_secret_access_key = YOUR_SECRET
```

### Problem: "Access Denied" to Bedrock

**Symptom:**
```
An error occurred (AccessDeniedException) when calling the InvokeModel operation
```

**Solutions:**

1. **Enable Model Access:**
   - Go to [AWS Bedrock Console](https://console.aws.amazon.com/bedrock/)
   - Click "Model access" in left sidebar
   - Click "Enable specific models"
   - Enable "Claude 3.5 Sonnet v2"
   - Save changes

2. **Check IAM Permissions:**
   Your IAM user/role needs these permissions:
   ```json
   {
     "Effect": "Allow",
     "Action": [
       "bedrock:InvokeModel",
       "bedrock:InvokeModelWithResponseStream"
     ],
     "Resource": "arn:aws:bedrock:*::foundation-model/anthropic.claude-3-5-sonnet-20241022-v2:0"
   }
   ```

3. **Verify Region:**
   Bedrock may not be available in all regions. Use `us-east-1` or `us-west-2`.

## Python/Installation Issues

### Problem: "Module not found"

**Symptom:**
```
ModuleNotFoundError: No module named 'boto3'
```

**Solution:**
```bash
# Ensure virtual environment is activated
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Verify installation
pip list | grep boto3
```

### Problem: Virtual Environment Not Activating

**macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

### Problem: Python Version Too Old

**Check version:**
```bash
python3 --version
```

**Need 3.9+**. If you have an older version:
- macOS: `brew install python@3.13`
- Ubuntu: `sudo apt install python3.13`
- Windows: Download from python.org

## Agent Runtime Issues

### Problem: "Invocation of model ID ... with on-demand throughput isn't supported"

**Symptom:**
```
ValidationException: Invocation of model ID anthropic.claude-3-5-sonnet-20241022-v2:0 
with on-demand throughput isn't supported. Retry your request with the ID or ARN of 
an inference profile that contains this model.
```

**Cause:** AWS Bedrock requires using inference profiles for Claude 3.5 Sonnet v2.

**Solution:** ✅ **FIXED!** The configuration has been updated to use the correct inference profile.

The model ID has been changed from:
- ❌ `anthropic.claude-3-5-sonnet-20241022-v2:0`
- ✅ `us.anthropic.claude-3-5-sonnet-20241022-v2:0`

**Alternative Models** (if the above doesn't work in your region):
Edit `config/agent_config.yaml` and try:
```yaml
model_id: "anthropic.claude-3-5-sonnet-20240620-v1:0"  # Claude 3.5 Sonnet v1
# or
model_id: "anthropic.claude-3-sonnet-20240229-v1:0"    # Claude 3 Sonnet
```

### Problem: "'AgentsforBedrockRuntime' object has no attribute 'converse'"

**Symptom:**
```
AttributeError: 'AgentsforBedrockRuntime' object has no attribute 'converse'
```

**Cause:** Wrong Bedrock client being used. The `converse` API is on `bedrock-runtime`, not `bedrock-agent-runtime`.

**Solution:** ✅ **FIXED!** The code has been updated to use the correct client.

If you still see this error:
1. Make sure you have the latest code
2. Restart your Python session
3. Verify boto3 is up to date: `pip install --upgrade boto3`

### Problem: "Too many requests" (ThrottlingException)

**Symptom:**
```
An error occurred (ThrottlingException) when calling the Converse operation: 
Too many requests, please wait before trying again.
```

**Cause:** AWS Bedrock rate limits. You've made too many API calls in a short time.

**Solution:**

**Immediate Fix:**
Just wait 30-60 seconds and try again. The rate limit will reset.

**Prevention:**
- Don't restart the agent repeatedly
- Wait a few seconds between messages
- AWS Bedrock has generous limits, but rapid testing can hit them

**For Production:**
The agent already has retry logic (max 4 retries). If you consistently hit limits:
1. Request a quota increase in AWS Service Quotas
2. Add exponential backoff (already implemented in boto3)
3. Consider using provisioned throughput

**Quick Test:**
```bash
# Wait 60 seconds
sleep 60

# Try again
python3 main.py
```

### Problem: "Unknown parameter in messages"

**Symptom:**
```
Parameter validation failed:
Unknown parameter in messages[0]: "timestamp", must be one of: role, content
Unknown parameter in messages[0]: "metadata", must be one of: role, content
```

**Cause:** Conversation memory was storing extra fields that Bedrock API doesn't accept.

**Solution:** ✅ **FIXED!** Memory module now stores only Bedrock-compatible fields (role, content).

If you still see this error:
1. Restart the agent (exit and run `python3 main.py` again)
2. The conversation history will be cleared with the new format

### Problem: "Requested resource not found" (DynamoDB)

**Symptom:**
```
An error occurred (ResourceNotFoundException) when calling the PutItem operation: 
Requested resource not found
```

**Cause:** Agent is configured to use DynamoDB for memory, but the table doesn't exist.

**Solution:** ✅ **FIXED!** The agent now uses local (in-memory) storage by default.

**For Production** (optional):
If you want persistent memory with DynamoDB:

1. Create the table:
```bash
aws dynamodb create-table \
    --table-name marketplace-agent-memory \
    --attribute-definitions AttributeName=session_id,AttributeType=S \
    --key-schema AttributeName=session_id,KeyType=HASH \
    --billing-mode PAY_PER_REQUEST \
    --region us-east-1
```

2. Update `agent/marketplace_agent.py`:
```python
self.memory_store = MemoryStore(
    backend="dynamodb",
    table_name="marketplace-agent-memory"
)
```

### Problem: "Knowledge base not found"

**Symptom:**
```
An error occurred (ResourceNotFoundException) when calling the Retrieve operation
```

**Solution:**

**Option 1: Run without Knowledge Base (Quick Test)**
The agent works without a Knowledge Base! Only KB queries will fail.

**Option 2: Create Knowledge Base**
1. Follow [GETTING_STARTED.md](GETTING_STARTED.md) Step 6
2. Update `config/agent_config.yaml` with your KB ID

### Problem: Agent Not Responding

**Check:**
1. AWS credentials are valid: `aws sts get-caller-identity`
2. Bedrock access enabled
3. No network issues
4. Check for error messages in console

**Debug mode:**
```python
# Add to main.py for debugging
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Problem: "Maximum iterations reached"

**Cause:** Agent is stuck in a tool execution loop.

**Solution:**
- This is a safety limit (default: 10 iterations)
- Usually means the model is confused
- Try rephrasing your question
- Or restart the conversation

## AWS Marketplace Issues

### Problem: "Access Denied" to Marketplace API

**Cause:** Your AWS account isn't registered as a Marketplace seller.

**Solution:**
1. Register as AWS Marketplace Seller
2. Or use the agent in simulation mode (it will work without real API access)

### Problem: Listing Creation Fails

**Check:**
1. All required fields provided
2. Validation passes: Use `validate_listing` action
3. AWS Marketplace seller account is active
4. Proper IAM permissions

## Testing & Verification

### Run Setup Test

```bash
python3 test_setup.py
```

Should show all checks passing:
```
✓ Python Version ................ PASS
✓ Dependencies .................. PASS
✓ Configuration Files ........... PASS
✓ Module Imports ................ PASS
```

### Test AWS Access

```bash
# Test credentials
aws sts get-caller-identity

# Test Bedrock access
aws bedrock list-foundation-models --region us-east-1

# Test Marketplace access (if registered)
aws marketplace-catalog list-entities \
  --catalog AWSMarketplace \
  --entity-type SaaSProduct
```

### Test Agent Import

```bash
python3 -c "from agent import MarketplaceListingAgent; print('✓ Import successful')"
```

## Common Error Messages

### "No module named 'agent'"

**Solution:**
```bash
# Ensure you're in the project directory
cd marketplace-listing-agent

# Activate virtual environment
source venv/bin/activate
```

### "boto3.exceptions.NoCredentialsError"

**Solution:**
```bash
# Configure AWS credentials
./setup_aws_credentials.sh
```

### "yaml.scanner.ScannerError"

**Cause:** YAML configuration file has syntax error.

**Solution:**
- Check `config/agent_config.yaml` for proper indentation
- YAML is whitespace-sensitive
- Use spaces, not tabs

## AI-Guided Workflow Issues

### Problem: Stuck at "Generating Listing content"

**Symptom:**
The AI-guided app hangs indefinitely at the "Generating listing content..." step.

**Cause:** 
This was a bug in the code flow where the pricing generation step was incorrectly nested inside a failure condition, causing the workflow to stop after successful content generation.

**Status:** ✅ **FIXED** (as of latest update)

**Solution:**
1. Make sure you have the latest version of `streamlit_guided_app.py`
2. Restart the Streamlit app:
   ```bash
   # Stop the app (Ctrl+C)
   streamlit run streamlit_guided_app.py
   ```

**If still experiencing issues:**
- Check your Bedrock model access: `python3 check_bedrock_models.py`
- Try a different model in the model selector
- Use the manual form workflow instead: `streamlit run streamlit_form_app.py`

### Problem: AI Generation Takes Too Long

**Symptom:**
Content generation takes more than 30 seconds.

**Causes:**
- Rate limiting on Bedrock API
- Large context being analyzed
- Model throttling

**Solutions:**
1. **Use a faster model:** Select Claude 3.5 Haiku in the model selector
2. **Reduce context:** Provide shorter product descriptions
3. **Wait it out:** First generation can take 20-30 seconds
4. **Use manual form:** For immediate control without AI delays

### Problem: "Product Title is too long" Error

**Symptom:**
```
ValidationException: String at /ProductTitle is too long (length: X, maximum allowed: 72)
```

**Cause:**
AWS Marketplace limits product titles to 72 characters, but the AI generated a longer title.

**Status:** ✅ **FIXED** - App now validates and truncates titles

**Solutions:**
1. **Automatic truncation:** The app now automatically truncates AI-generated titles to 72 chars
2. **Manual edit:** Edit the title in the review screen before submitting
3. **Validation:** The app now shows an error if you try to submit a title > 72 chars

**Tips for good titles:**
- Keep it under 60 characters for best display
- Focus on product name and key differentiator
- Avoid long descriptive phrases
- Example: "CloudSync Pro - Real-time File Sync" (39 chars) ✅
- Not: "CloudSync Pro - Cloud-Native Security & Compliance Management Platform for Containers & Multi-Cloud" (95 chars) ❌

### Problem: "ResourceInUseException" - Entity Locked

**Symptom:**
```
ResourceInUseException: Requested change set has entities locked by change sets
```

**Cause:**
AWS Marketplace locks entities while processing changesets. This can happen when:
- Stage 1 creates and updates the product (2 changesets)
- Stage 2 tries to run before Stage 1's update completes
- Multiple changesets are submitted too quickly

**Status:** ✅ **FIXED** - App now waits for changesets and retries

**Solutions:**
1. **Automatic retry:** The app now retries up to 3 times with 5-second delays
2. **Wait for completion:** Stage 1 now waits for update changeset to complete
3. **Manual retry:** If it still fails, wait 10-20 seconds and try the stage again

**Prevention:**
- The app now waits for each changeset to complete before proceeding
- Retry logic handles temporary locks automatically

## Getting Help

### Quick Checks

1. ✅ Python 3.9+ installed: `python3 --version`
2. ✅ Virtual environment activated: `which python`
3. ✅ Dependencies installed: `pip list | grep boto3`
4. ✅ AWS credentials valid: `aws sts get-caller-identity`
5. ✅ In project directory: `ls main.py`

### Diagnostic Commands

```bash
# Full system check
python3 test_setup.py

# Check AWS configuration
aws configure list

# Check Python packages
pip list

# Check file permissions
ls -la ~/.aws/
```

### Still Stuck?

1. Check [GETTING_STARTED.md](GETTING_STARTED.md) for detailed setup
2. Review [docs/SETUP_GUIDE.md](docs/SETUP_GUIDE.md)
3. Verify all prerequisites in [START_HERE.md](START_HERE.md)

## Quick Fixes Summary

| Problem | Quick Fix |
|---------|-----------|
| Expired token | `./setup_aws_credentials.sh` |
| Module not found | `pip install -r requirements.txt` |
| Bedrock access denied | Enable model in Bedrock console |
| Parse error | Run `./setup_aws_credentials.sh` |
| KB not found | Agent works without KB |
| Import error | `cd marketplace-listing-agent && source venv/bin/activate` |

---

**Most Common Issue:** Expired AWS credentials
**Quick Fix:** Run `./setup_aws_credentials.sh` and get fresh credentials
