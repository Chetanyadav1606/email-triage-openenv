# How to Use Real Kaggle Data

## Quick Setup

### Option 1: Automatic (Recommended)
The system will automatically:
1. Check for local Kaggle data
2. Fall back to synthetic data if not found
3. Augment labels automatically

### Option 2: Manual - Using Kaggle API

#### Step 1: Install Kaggle
```bash
pip install kaggle
```

#### Step 2: Get API Credentials
1. Go to https://www.kaggle.com/settings/account
2. Click "Create New Token" 
3. A file `kaggle.json` will download
4. Place it in `~/.kaggle/kaggle.json`
5. Set permissions: `chmod 600 ~/.kaggle/kaggle.json`

#### Step 3: Download Dataset
```bash
# Download Enron emails (most realistic for this task)
kaggle datasets download -d wcukierski/enron-email-dataset

# Or SpamAssassin dataset
kaggle datasets download -d wanderfj/spam-e-mail-detection-dataset

# Extract to data folder
unzip enron-email-dataset.zip -d data/
```

#### Step 4: Convert to Our Format (Optional)
```python
from data_loader import DatasetLoader

loader = DatasetLoader()
# Automatically loads from data/ folder
emails = loader.load_local_csv("path/to/your/emails.csv")
```

## Using Local CSV Files

### Format Your CSV
Create a CSV with these columns:
```
id,subject,body,customer_id,customer_tier,true_label,true_priority,true_response
1,Payment Issue,Card was declined...,C1,premium,billing,high,We'll help you...
```

### Column Descriptions
- **id**: Unique email identifier
- **subject**: Email subject line
- **body**: Email content
- **customer_id**: Customer identifier
- **customer_tier**: free, premium, or enterprise
- **true_label**: billing, technical, feature, or general
- **true_priority**: low, medium, or high
- **true_response**: Expected/ground truth response

### Load Using API
```python
from data_loader import DatasetLoader
from environment import EmailEnv

loader = DatasetLoader()
emails = loader.load_local_csv("my_emails.csv")
env = EmailEnv(emails)
```

## Available Kaggle Datasets

### 1. Enron Email Dataset (Recommended!)
- **Dataset**: wcukierski/enron-email-dataset
- **Size**: ~500K emails
- **Real-world**: Actual corporate emails
- **Best for**: Realistic scenarios

### 2. SpamAssassin
- **Dataset**: wanderfj/spam-e-mail-detection-dataset
- **Size**: ~6K emails
- **Type**: Spam vs Ham classification
- **Best for**: Spam detection tasks

### 3. Customer Support Helpdesk Tickets
- **Dataset**: Various on Kaggle
- **Size**: Variable
- **Type**: Support tickets with resolutions
- **Best for**: Our use case

## Augmentation

The system automatically:
```python
# Augments emails with smart labels based on content
loader.augment_emails_with_labels(emails)
```

This analyzes **subject + body** and assigns:
- **Category**: Based on keywords (billing, technical, etc.)
- **Priority**: Based on urgency indicators
- **Tier**: Randomly distributed (free/premium/enterprise)

## Example: Using Enron Data in Your App

```python
#!/usr/bin/env python3
from data_loader import DatasetLoader
from environment import EmailEnv
from task_suite import TaskSuite

# Load real Enron data
loader = DatasetLoader()
try:
    emails = loader.load_kaggle_dataset("wcukierski/enron-email-dataset", limit=100)
except:
    # Falls back to synthetic if Kaggle not available
    emails = loader._get_fallback_emails(limit=20)

# Create environment
env = EmailEnv(emails)
state = env.reset()

print(f"Processing {len(emails)} emails")
print(f"First email: {state.current_email.subject}")
```

## Troubleshooting

### "Kaggle API not installed"
```bash
pip install kaggle
```

### "Couldn't authenticate Kaggle API"
- Check `~/.kaggle/kaggle.json` exists
- Verify permissions: `chmod 600`
- Regenerate token on kaggle.com

### "Dataset not found"
- Check dataset name is correct
- Ensure you're logged into Kaggle
- Check internet connection

### No real data, using fallback
- This is OK! System falls back gracefully
- Synthetic data includes 10 realistic scenarios
- Add your own CSV for customization

## Creating Your Own Dataset

### Step 1: Collect Emails
- Export from your email system
- Format as CSV with required columns
- Ensure diversity of categories

### Step 2: Label Ground Truth
```python
# Use grader to verify labels
from task_suite import TaskSuite

grader = TaskSuite.create_grader_for_task("easy")
# Your grader can verify labels
```

### Step 3: Use in Training
```python
loader = DatasetLoader()
emails = loader.load_local_csv("my_company_emails.csv")
env = EmailEnv(emails)
# Train agent!
```

## Performance Tips

### For Better Training
1. **Use 50-100 emails** per task
2. **Mix difficulties**: varied subject lengths, clarity
3. **Real customer data**: better than synthetic
4. **Balanced labels**: ~25% per category

### For Evaluation
1. **Hold-out test set**: 20% of data
2. **Reproducible splits**: Use `DatasetLoader.split_train_test()`
3. **Multiple runs**: Average scores across runs

## Example Data Statistics

```python
from data_loader import DatasetLoader

loader = DatasetLoader()
emails = loader.load_kaggle_dataset("wcukierski/enron-email-dataset", limit=100)

# Analyze
categories = {}
for email in emails:
    label = email.true_label
    categories[label] = categories.get(label, 0) + 1

print(f"Category distribution: {categories}")
# Expected: ~25% each (billing, technical, feature, general)
```

## Next Steps

1. Load your data (real or CSV)
2. Run baseline: `python baseline_inference.py`
3. Check results: `baseline_results.json`
4. Train your agent!

---

**Questions?** Check API_REFERENCE.md or DEVELOPMENT.md
