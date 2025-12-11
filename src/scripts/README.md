# MynEra Aira Scripts

Production scripts for data generation, ingestion, and system maintenance.

---

## 📁 Available Scripts

### `generate_seed_data.py`
**Purpose:** Generate realistic seed data with market simulation.

**Output:**
- `data/mentors.json` - 120 mentors
- `data/courses.json` - 268 courses  
- `data/learners.json` - 960 learners

**Usage:**
```bash
python src/scripts/generate_seed_data.py
```

**Features:**
- Azerbaijani names and companies
- Skill-based pricing algorithm
- Organic enrollment simulation
- Realistic market dynamics

---

### `ingest_data.py`
**Purpose:** Load data from JSON into Qdrant with surgical embeddings.

**Usage:**
```bash
python src/scripts/ingest_data.py
```

**What it does:**
1. Loads courses from `data/courses.json`
2. Generates surgical embeddings (semantic fields only)
3. Uploads to Qdrant `courses_collection`
4. Repeats for mentors

**Requirements:**
- Qdrant connection configured in `.env`
- Data files must exist (run `generate_seed_data.py` first)

---

### `system_check.py`
**Purpose:** Comprehensive system health verification.

**Usage:**
```bash
python src/scripts/system_check.py
```

**Checks:**
1. ✅ Data files present
2. ✅ Qdrant connection working
3. ✅ Vector collections populated
4. ✅ Semantic search functional

**Exit codes:**
- `0` - All checks passed
- `1` - One or more checks failed

---

### `cleanup_project.py`
**Purpose:** Remove temporary development files.

**Usage:**
```bash
python src/scripts/cleanup_project.py
```

**Deletes:**
- Documentation artifacts
- Test scripts
- Verification files

**Keeps:**
- All source code
- Production scripts
- Data files

---

## 🔄 Typical Workflow

### 1. Initial Setup
```bash
# Generate data
python src/scripts/generate_seed_data.py

# Load to Qdrant
python src/scripts/ingest_data.py

# Verify everything
python src/scripts/system_check.py
```

### 2. Data Refresh
```bash
# Regenerate with new random data
python src/scripts/generate_seed_data.py

# Re-upload to Qdrant
python src/scripts/ingest_data.py
```

### 3. Health Check
```bash
# Anytime you want to verify system status
python src/scripts/system_check.py
```

### 4. Project Cleanup
```bash
# Remove temporary files
python src/scripts/cleanup_project.py
```

---

## 🎯 Best Practices

**Before testing:**
```bash
python src/scripts/system_check.py
```

**After code changes:**
```bash
python src/scripts/ingest_data.py  # If data logic changed
python src/scripts/system_check.py  # Verify still working
```

**Before deployment:**
```bash
python src/scripts/cleanup_project.py  # Clean up
python src/scripts/system_check.py     # Final verification
```

---

## 📊 Script Dependencies

```
generate_seed_data.py
    ↓
ingest_data.py
    ↓
system_check.py
```

**Always run in this order for initial setup!**

---

## 🔧 Troubleshooting

### Error: "File not found: courses.json"
**Solution:** Run `generate_seed_data.py` first

### Error: "Failed to connect to Qdrant"
**Solution:** 
- Check `.env` for correct credentials
- Ensure Qdrant service is running
- Verify network connectivity

### Error: "Collection not found"
**Solution:** Run `ingest_data.py` to create collections

### Warning: "0 vectors in collection"
**Solution:** Run `ingest_data.py` to populate

---

## 💡 Tips

- Run `system_check.py` regularly to catch issues early
- Use `cleanup_project.py` before committing to git
- Regenerate data periodically for diverse test cases
- Check script output for helpful next-step suggestions

---

**Maintained by:** MynEra Aira Team  
**Last Updated:** 2025-12-11
