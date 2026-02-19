import csv
import os
import shutil
import argparse
from collections import defaultdict

def normalize(text):
    return text.strip().lower()

def check_duplicates(files):
    print("Checking for duplicates where (Title+Company+Location) match but Links differ...")
    
    # Dictionary to store jobs grouped by (Title, Company, Location)
    grouped_jobs = defaultdict(list)

    for filename in files:
        try:
            with open(filename, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    title = normalize(row.get('Title', ''))
                    company = normalize(row.get('Company', ''))
                    location = normalize(row.get('Location', ''))
                    link = row.get('Link', '').strip()
                    
                    key = (title, company, location)
                    grouped_jobs[key].append({
                        'Title': row.get('Title', ''),
                        'Company': row.get('Company', ''),
                        'Location': row.get('Location', ''),
                        'Link': link,
                        'Source': filename
                    })
        except FileNotFoundError:
            print(f"Error: File {filename} not found.")
            return

    duplicates_found = False
    
    for key, jobs in grouped_jobs.items():
        # Get unique links for this group
        unique_links = set(job['Link'] for job in jobs)
        
        if len(unique_links) > 1:
            duplicates_found = True
            title, company, location = key
            print(f"\n--- Duplicate Job Found ---")
            print(f"Title: {jobs[0]['Title']}")
            print(f"Company: {jobs[0]['Company']}")
            print(f"Location: {jobs[0]['Location']}")
            print(f"Different Links ({len(unique_links)}):")
            for job in jobs:
                print(f"  - Link: {job['Link']} (from {job['Source']})")

    if not duplicates_found:
        print("\nNo duplicates with different links found based on Title+Company+Location.")

def remove_duplicates(files):
    for filename in files:
        print(f"Processing {filename}...")
        temp_filename = filename + '.tmp'
        
        unique_jobs = set()
        kept_count = 0
        removed_count = 0
        
        try:
            with open(filename, 'r', encoding='utf-8-sig') as f_in, \
                 open(temp_filename, 'w', encoding='utf-8-sig', newline='') as f_out:
                
                reader = csv.DictReader(f_in)
                fieldnames = reader.fieldnames
                writer = csv.DictWriter(f_out, fieldnames=fieldnames)
                writer.writeheader()
                
                for row in reader:
                    title = normalize(row.get('Title', ''))
                    company = normalize(row.get('Company', ''))
                    location = normalize(row.get('Location', ''))
                    
                    # Check based on Title + Company + Location
                    key = (title, company, location)
                    
                    if key in unique_jobs:
                        removed_count += 1
                    else:
                        unique_jobs.add(key)
                        writer.writerow(row)
                        kept_count += 1
                        
            # Replace original file with temp file
            shutil.move(temp_filename, filename)
            print(f"  Finished. Kept: {kept_count}, Removed: {removed_count}")
            
        except FileNotFoundError:
            print(f"Error: File {filename} not found.")
        except Exception as e:
            print(f"Error processing {filename}: {e}")
            if os.path.exists(temp_filename):
                os.remove(temp_filename)

def main():
    parser = argparse.ArgumentParser(description="Manage duplicate jobs in CSV files.")
    parser.add_argument('action', choices=['check', 'remove'], help="Action to perform: 'check' or 'remove'")
    parser.add_argument('--files', nargs='+', default=['jobsdb_result_all.csv', 'jobsdb_full_data.csv'], help="List of files to process")
    
    args = parser.parse_args()
    
    if args.action == 'check':
        check_duplicates(args.files)
    elif args.action == 'remove':
        remove_duplicates(args.files)

if __name__ == "__main__":
    main()
