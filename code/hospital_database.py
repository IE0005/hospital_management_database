import sqlite3
from faker import Faker
from datetime import datetime, timedelta
import random
import pandas as pd


fake = Faker()


conn = sqlite3.connect("hospital_management.db")
cursor = conn.cursor()


cursor.execute("""
CREATE TABLE IF NOT EXISTS Patient (
    patient_id INTEGER PRIMARY KEY,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    dob DATE NOT NULL,
    gender TEXT NOT NULL,
    address TEXT,
    phone TEXT,
    insurance_info TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS Doctor (
    doctor_id INTEGER PRIMARY KEY,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    specialization TEXT NOT NULL,
    schedule TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS Appointment (
    appointment_id INTEGER PRIMARY KEY,
    patient_id INTEGER NOT NULL,
    doctor_id INTEGER NOT NULL,
    appointment_date DATETIME NOT NULL,
    status TEXT NOT NULL,
    machine_id INTEGER,
    FOREIGN KEY (patient_id) REFERENCES Patient(patient_id),
    FOREIGN KEY (doctor_id) REFERENCES Doctor(doctor_id),
    FOREIGN KEY (machine_id) REFERENCES MachineInventory(machine_id)
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS Billing (
    billing_id INTEGER PRIMARY KEY,
    patient_id INTEGER NOT NULL,
    amount REAL NOT NULL,
    billing_date DATE NOT NULL,
    payment_status TEXT NOT NULL,
    FOREIGN KEY (patient_id) REFERENCES Patient(patient_id)
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS Inventory (
    inventory_id INTEGER PRIMARY KEY,
    item_name TEXT NOT NULL,
    quantity INTEGER NOT NULL,
    expiration_date DATE
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS MachineInventory (
    machine_id INTEGER PRIMARY KEY,
    machine_name TEXT NOT NULL,
    availability_status TEXT NOT NULL,
    location TEXT,
    last_maintenance_date DATE,
    next_maintenance_date DATE,
    inventory_id INTEGER NOT NULL,
    FOREIGN KEY (inventory_id) REFERENCES Inventory(inventory_id)
)
""")

print("Database schema created successfully.")



for _ in range(50):
    cursor.execute("""
    INSERT INTO Patient (first_name, last_name, dob, gender, address, phone, insurance_info)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        fake.first_name(),
        fake.last_name(),
        fake.date_of_birth(minimum_age=1, maximum_age=90),
        random.choice(["Male", "Female", "Other"]),
        fake.address(),
        fake.phone_number(),
        random.choice(["Private", "Public", "None"])
    ))

specializations = ["Cardiology", "Neurology", "Pediatrics", "Orthopedics", "General Medicine"]
for _ in range(20):
    cursor.execute("""
    INSERT INTO Doctor (first_name, last_name, specialization, schedule)
    VALUES (?, ?, ?, ?)
    """, (
        fake.first_name(),
        fake.last_name(),
        random.choice(specializations),
        fake.text(max_nb_chars=50)
    ))


for _ in range(10):
    cursor.execute("""
    INSERT INTO Inventory (item_name, quantity, expiration_date)
    VALUES (?, ?, ?)
    """, (
        fake.word(),
        random.randint(1, 100),
        fake.date_between(start_date='today', end_date='+6y')
    ))

equipment = [
    {"name": "X-Ray Machine", "quantity": 5},
    {"name": "MRI Scanner", "quantity": 3},
    {"name": "Ventilator", "quantity": 10},
    {"name": "ECG Machine", "quantity": 8},
    {"name": "Defibrillator", "quantity": 6},
]
locations = ["ER Room 1", "ER Room 2", "ER Room 3", "Radiology", "ICU"]
inventory_ids = [row[0] for row in cursor.execute("SELECT inventory_id FROM Inventory").fetchall()]
for equipment_item in equipment:
    for _ in range(equipment_item["quantity"]):
        cursor.execute("""
        INSERT INTO MachineInventory (machine_name, availability_status, location, last_maintenance_date, next_maintenance_date, inventory_id)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (
            equipment_item["name"],
            random.choice(["Available", "In Maintenance", "Unavailable"]),
            random.choice(locations),
            fake.date_between(start_date='-1y', end_date='today'),
            fake.date_between(start_date='today', end_date='+1y'),
            random.choice(inventory_ids)
        ))


patient_ids = [row[0] for row in cursor.execute("SELECT patient_id FROM Patient").fetchall()]
doctor_ids = [row[0] for row in cursor.execute("SELECT doctor_id FROM Doctor").fetchall()]
machine_ids = [row[0] for row in cursor.execute("SELECT machine_id FROM MachineInventory").fetchall()]
for _ in range(100):
    cursor.execute("""
    INSERT INTO Appointment (patient_id, doctor_id, appointment_date, status, machine_id)
    VALUES (?, ?, ?, ?, ?)
    """, (
        random.choice(patient_ids),
        random.choice(doctor_ids),
        fake.date_time_between(start_date='now', end_date='+7d'),
        random.choice(["Scheduled", "Completed", "Cancelled"]),
        random.choice(machine_ids)
    ))


for patient_id in patient_ids:
    cursor.execute("""
    INSERT INTO Billing (patient_id, amount, billing_date, payment_status)
    VALUES (?, ?, ?, ?)
    """, (
        patient_id,
        round(random.uniform(50, 5000), 2),
        fake.date_between(start_date='-6m', end_date='today'),
        random.choice(["Paid", "Unpaid", "Pending"])
    ))

conn.commit()
print("Data populated successfully.")


def display_schema():
    cursor.execute("SELECT name, sql FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    for table in tables:
        print(f"Table Name: {table[0]}")
        print(f"Schema:\n{table[1]}")
        print("-" * 50)

display_schema()


cursor.execute("""
SELECT
    p.first_name AS patient_first_name,
    p.last_name AS patient_last_name,
    p.insurance_info AS patient_insurance_info,
    a.appointment_date,
    a.status AS appointment_status,
    d.first_name AS doctor_first_name,
    d.last_name AS doctor_last_name,
    b.amount AS billing_amount,
    b.payment_status
FROM
    Patient p
LEFT JOIN
    Appointment a ON p.patient_id = a.patient_id
LEFT JOIN
    Doctor d ON a.doctor_id = d.doctor_id
LEFT JOIN
    Billing b ON p.patient_id = b.patient_id
""")

rows = cursor.fetchall()
columns = [desc[0] for desc in cursor.description]
data = pd.DataFrame(rows, columns=columns)
print("\nPatient information with appointments and billing:")
print(data)

cursor.execute("SELECT COUNT(*) FROM Patient")
num_patients = cursor.fetchone()[0]


cursor.execute("SELECT COUNT(*) FROM Doctor")
num_doctors = cursor.fetchone()[0]

print(f"Number of patients: {num_patients}")
print(f"Number of doctors: {num_doctors}")

conn.close()
print("Database closed.")
