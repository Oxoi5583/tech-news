python -m pip install -r requirements.txt
git fetch --all && git reset --hard origin/$(git branch --show-current)
python build.py --source "./papers" --output "/var/wiki/html/tech_news"
