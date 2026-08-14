#!/bin/bash
cd /workspace/aarkaai3b

# 1. Create a backup of existing files
echo "Creating backup of current files..."
if [ -f config.py ]; then
    tar -czf backup_$(date +%Y%m%d_%H%M%S).tar.gz config.py database.py main.py pipeline.py register_visitor.py schemas.py modules/aarkaa_engine.py modules/auto_learn.py modules/finance.py modules/memory.py modules/options_strategy.py modules/subscription.py modules/technical.py modules/web_search.py modules/semantic_filter.py || true
else
    echo "No existing files to backup, skipping."
fi

# Install unzip if not present
if ! command -v unzip &> /dev/null; then
    echo "unzip not found, installing..."
    apt-get update && apt-get install -y unzip
fi

# 2. Extract update zip
echo "Extracting updated files..."
unzip -o aarkaai_update.zip
rm -f aarkaai_update.zip

# 2.5. Install dependencies (requirements + skill deps)
echo "Installing dependencies..."
python3.13 -m pip install --quiet -r requirements.txt 2>&1 | tail -5
python3.13 -m pip install --quiet chromadb python-docx python-pptx openpyxl pdfplumber pypdf reportlab pyyaml xlsxwriter weasyprint matplotlib 2>&1 | tail -5

# 3. Run database migrations (only if migration script was sent)
echo "Checking for database migrations..."
if [ -f migrate_add_role.py ]; then
    echo "Running RBAC migration..."
    python3.13 migrate_add_role.py
fi

# 3.6. Run ChromaDB migration (SQLite blobs → ChromaDB)
echo "Checking for ChromaDB migration..."
echo "Skipping ChromaDB migration (already completed)."

# 3.8. Run AARKAA-VISION standalone model merging if not already done
if [ ! -d "aarkaa-vision-standalone" ]; then
    echo "Fusing base SD 1.4 model and custom LoRA into a standalone model..."
    python3.13 merge_lora.py
fi

# 3.9 Run system design knowledge indexing
echo "Running system design knowledge indexing..."
python3.13 -m scratch.insert_expert_sysdesign || true

# 4. Configure Nginx
echo "Configuring Nginx..."
if [ -f nginx_site.conf ]; then
    sudo cp nginx_site.conf /etc/nginx/sites-enabled/aarkaai
    sudo nginx -t && sudo systemctl reload nginx
fi

# 5. Restart backend service
echo "Restarting backend..."
fuser -k 5000/tcp 2>/dev/null || true
pkill -9 -f "uvicorn main:app" 2>/dev/null || true
sleep 1

# Start application in background
if [ ! -f .env.production ]; then
    cp .env.production.template .env.production
fi
nohup env AARKAAI_IDLE_TIMEOUT=300 python3.13 -m uvicorn main:app --host 0.0.0.0 --port 5000 --workers 1 --env-file .env.production > aarkaai.log 2>&1 </dev/null &
echo "Started aarkaai in background."

