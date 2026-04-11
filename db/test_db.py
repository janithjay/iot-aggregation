from database import *

# Test insert
insert_record("1", "sensor_A", "file1.json")

# Test status update
update_record_status("1", "processing")

# Test summary update
update_record_summary("1", {"min": 10, "max": 30, "avg": 20})

# Test get one record
print(get_record("1"))

# Test list all
print(list_records())