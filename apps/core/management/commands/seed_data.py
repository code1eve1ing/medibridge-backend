"""
Management command: python manage.py seed_data

Creates dummy users, doctor profiles, patient profiles, hospitals, and surgery packages
for local development. Safe to run multiple times — skips records that already exist.

Demo credentials (all passwords: Test@1234):
  admin@test.local           — Admin
  patient@test.local         — Patient (Sarah Johnson)
  patient2@test.local        — Patient (John Doe)
  dr.sharma@test.local       — Doctor (Cardiology, 18 yrs)
  dr.kapoor@test.local       — Doctor (Cardiology, 3 yrs)
  dr.patel@test.local        — Doctor (Orthopedics, 13 yrs)
  dr.nair@test.local         — Doctor (Orthopedics, 5 yrs)
  dr.mehta@test.local        — Doctor (Neurology, 11 yrs)
  dr.krishna@test.local      — Doctor (Neurology, 22 yrs)
  dr.roy@test.local          — Doctor (Oncology, 15 yrs)
  dr.gupta@test.local        — Doctor (Oncology, 7 yrs)
  dr.malhotra@test.local     — Doctor (General Surgery, 9 yrs)
  dr.pillai@test.local       — Doctor (General Surgery, 2 yrs)
  dr.joshi@test.local        — Doctor (Gastroenterology, 14 yrs)
  dr.bose@test.local         — Doctor (Gastroenterology, 4 yrs)
  dr.mishra@test.local       — Doctor (Gynecology, 17 yrs)
  dr.agarwal@test.local      — Doctor (Gynecology, 5 yrs)
  dr.verma@test.local        — Doctor (Ophthalmology, 10 yrs)
  dr.sinha@test.local        — Doctor (Ophthalmology, 3 yrs)
  dr.reddy@test.local        — Doctor (Pulmonology, 15 yrs)
  dr.iyer@test.local         — Doctor (Pulmonology, 6 yrs)
  dr.pandey@test.local       — Doctor (Urology, 12 yrs)
  dr.chandra@test.local      — Doctor (Urology, 4 yrs)
  dr.saxena@test.local       — Doctor (ENT Surgery, 11 yrs)
  dr.desai@test.local        — Doctor (ENT Surgery, 4 yrs)
  dr.chatterjee@test.local   — Doctor (Neurosurgery, 13 yrs)
  dr.tiwari@test.local       — Doctor (Neurosurgery, 5 yrs)
"""

import datetime
import secrets

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.accounts.models import User
from apps.patients.models import PatientProfile
from apps.doctors.models import DoctorProfile, DoctorEducation, DoctorAvailabilitySlot, Specialization
from apps.hospitals.models import Hospital, SurgeryPackage
from apps.consultations.models import (
    SymptomIntake, Appointment, Prescription, PrescriptionMedicine, PrescribedTest,
)
from apps.surgery.models import (
    SurgeryRecommendation, SurgeryPackageBooking, RecommendationMessage,
)


PASSWORD = "Test@1234"

SPECIALIZATIONS = [
    {"name": "Cardiology",         "slug": "cardiology"},
    {"name": "Orthopedics",        "slug": "orthopedics"},
    {"name": "Neurology",          "slug": "neurology"},
    {"name": "Oncology",           "slug": "oncology"},
    {"name": "General Surgery",    "slug": "general-surgery"},
    {"name": "Gastroenterology",   "slug": "gastroenterology"},
    {"name": "Gynecology",         "slug": "gynecology"},
    {"name": "Ophthalmology",      "slug": "ophthalmology"},
    {"name": "Pulmonology",        "slug": "pulmonology"},
    {"name": "Urology",            "slug": "urology"},
    {"name": "ENT",                "slug": "ent"},
    {"name": "ENT Surgery",        "slug": "ent-surgery"},
    {"name": "Neurosurgery",       "slug": "neurosurgery"},
    {"name": "Spine Surgery",      "slug": "spine-surgery"},
    {"name": "Transplant Surgery", "slug": "transplant-surgery"},
    {"name": "Dermatology",        "slug": "dermatology"},
    {"name": "Endocrinology",      "slug": "endocrinology"},
    {"name": "Family Medicine",    "slug": "family-medicine"},
    {"name": "Internal Medicine",  "slug": "internal-medicine"},
    {"name": "Nephrology",         "slug": "nephrology"},
    {"name": "Pediatrics",         "slug": "pediatrics"},
    {"name": "Psychiatry",         "slug": "psychiatry"},
]

DOCTORS = [
    # ── Cardiology ─────────────────────────────────────────────────────────────
    {
        "email": "dr.sharma@test.local",
        "first_name": "Rajesh",
        "last_name": "Sharma",
        "phone": "+91-9876543210",
        "bio": (
            "Dr. Rajesh Sharma is a senior interventional cardiologist with 18 years of experience "
            "at Apollo Hospitals, New Delhi. He specialises in complex coronary interventions, "
            "structural heart disease, and preventive cardiology."
        ),
        "medical_council_reg_no": "MCI-2006-DL-04821",
        "years_of_experience": 18,
        "consultation_fee_usd": "80.00",
        "consultation_duration_min": 30,
        "languages": "English, Hindi",
        "hospital_affiliation": "Apollo Hospitals, New Delhi",
        "timezone": "Asia/Kolkata",
        "specializations": ["Cardiology"],
        "education": [
            {"degree": "MBBS", "institution": "AIIMS New Delhi", "year_completed": 2001},
            {"degree": "MD (Internal Medicine)", "institution": "AIIMS New Delhi", "year_completed": 2004},
            {"degree": "DM (Cardiology)", "institution": "PGI Chandigarh", "year_completed": 2006},
        ],
        "slots": [
            {"day": 0, "start": "09:00", "end": "13:00"},
            {"day": 1, "start": "09:00", "end": "13:00"},
            {"day": 2, "start": "09:00", "end": "13:00"},
            {"day": 3, "start": "14:00", "end": "18:00"},
            {"day": 4, "start": "09:00", "end": "13:00"},
        ],
    },
    {
        "email": "dr.kapoor@test.local",
        "first_name": "Arjun",
        "last_name": "Kapoor",
        "phone": "+91-9876500101",
        "bio": (
            "Dr. Arjun Kapoor is a junior cardiologist with 3 years of clinical experience at "
            "Narayana Health, Bangalore. He trained under internationally recognized cardiac "
            "surgeons and focuses on non-invasive cardiology and heart failure management."
        ),
        "medical_council_reg_no": "MCI-2021-KA-30145",
        "years_of_experience": 3,
        "consultation_fee_usd": "45.00",
        "consultation_duration_min": 30,
        "languages": "English, Hindi, Kannada",
        "hospital_affiliation": "Narayana Health, Bangalore",
        "timezone": "Asia/Kolkata",
        "specializations": ["Cardiology"],
        "education": [
            {"degree": "MBBS", "institution": "Bangalore Medical College", "year_completed": 2017},
            {"degree": "MD (Medicine)", "institution": "Manipal Academy of Higher Education", "year_completed": 2020},
            {"degree": "DNB (Cardiology)", "institution": "Narayana Health, Bangalore", "year_completed": 2023},
        ],
        "slots": [
            {"day": 1, "start": "10:00", "end": "14:00"},
            {"day": 3, "start": "10:00", "end": "14:00"},
            {"day": 5, "start": "09:00", "end": "12:00"},
        ],
    },
    # ── Orthopedics ────────────────────────────────────────────────────────────
    {
        "email": "dr.patel@test.local",
        "first_name": "Priya",
        "last_name": "Patel",
        "phone": "+91-9876543211",
        "bio": (
            "Dr. Priya Patel is an orthopaedic surgeon specialising in joint replacement and "
            "sports injuries. With 13 years of practice at Fortis Healthcare Mumbai, she has "
            "performed over 2,000 knee and hip replacement surgeries."
        ),
        "medical_council_reg_no": "MCI-2011-MH-08134",
        "years_of_experience": 13,
        "consultation_fee_usd": "70.00",
        "consultation_duration_min": 45,
        "languages": "English, Gujarati, Hindi",
        "hospital_affiliation": "Fortis Healthcare, Mumbai",
        "timezone": "Asia/Kolkata",
        "specializations": ["Orthopedics"],
        "education": [
            {"degree": "MBBS", "institution": "Grant Medical College, Mumbai", "year_completed": 2006},
            {"degree": "MS (Orthopaedics)", "institution": "KEM Hospital, Mumbai", "year_completed": 2011},
            {"degree": "Fellowship in Joint Replacement", "institution": "Royal National Orthopaedic Hospital, UK", "year_completed": 2012},
        ],
        "slots": [
            {"day": 1, "start": "10:00", "end": "14:00"},
            {"day": 2, "start": "10:00", "end": "14:00"},
            {"day": 3, "start": "10:00", "end": "14:00"},
            {"day": 4, "start": "10:00", "end": "14:00"},
            {"day": 5, "start": "09:00", "end": "12:00"},
        ],
    },
    {
        "email": "dr.nair@test.local",
        "first_name": "Deepa",
        "last_name": "Nair",
        "phone": "+91-9876500102",
        "bio": (
            "Dr. Deepa Nair is an orthopaedic surgeon with 5 years of experience specialising in "
            "minimally invasive joint procedures and paediatric orthopaedics at Narayana Health, "
            "Bangalore. She trained with leading joint replacement surgeons in South India."
        ),
        "medical_council_reg_no": "MCI-2019-KA-27800",
        "years_of_experience": 5,
        "consultation_fee_usd": "50.00",
        "consultation_duration_min": 30,
        "languages": "English, Malayalam, Kannada",
        "hospital_affiliation": "Narayana Health, Bangalore",
        "timezone": "Asia/Kolkata",
        "specializations": ["Orthopedics"],
        "education": [
            {"degree": "MBBS", "institution": "Amrita Institute of Medical Sciences, Kochi", "year_completed": 2015},
            {"degree": "MS (Orthopaedics)", "institution": "JIPMER, Puducherry", "year_completed": 2019},
        ],
        "slots": [
            {"day": 0, "start": "09:00", "end": "13:00"},
            {"day": 2, "start": "09:00", "end": "13:00"},
            {"day": 4, "start": "09:00", "end": "13:00"},
        ],
    },
    # ── Neurology ──────────────────────────────────────────────────────────────
    {
        "email": "dr.mehta@test.local",
        "first_name": "Amit",
        "last_name": "Mehta",
        "phone": "+91-9876543212",
        "bio": (
            "Dr. Amit Mehta is a neurologist and epileptologist at Manipal Hospital Bangalore. "
            "He has 11 years of experience managing stroke, epilepsy, movement disorders, and "
            "neurodegenerative diseases, and leads a dedicated stroke unit."
        ),
        "medical_council_reg_no": "MCI-2013-KA-11259",
        "years_of_experience": 11,
        "consultation_fee_usd": "75.00",
        "consultation_duration_min": 30,
        "languages": "English, Kannada, Hindi",
        "hospital_affiliation": "Manipal Hospital, Bangalore",
        "timezone": "Asia/Kolkata",
        "specializations": ["Neurology"],
        "education": [
            {"degree": "MBBS", "institution": "Bangalore Medical College", "year_completed": 2008},
            {"degree": "MD (General Medicine)", "institution": "St. John's Medical College, Bangalore", "year_completed": 2011},
            {"degree": "DM (Neurology)", "institution": "NIMHANS, Bangalore", "year_completed": 2013},
        ],
        "slots": [
            {"day": 0, "start": "14:00", "end": "18:00"},
            {"day": 2, "start": "14:00", "end": "18:00"},
            {"day": 4, "start": "14:00", "end": "18:00"},
        ],
    },
    {
        "email": "dr.krishna@test.local",
        "first_name": "Venkata",
        "last_name": "Krishna",
        "phone": "+91-9876500103",
        "bio": (
            "Dr. Venkata Krishna is a veteran neurologist with 22 years of experience, currently "
            "senior consultant at Max Super Speciality Hospital, New Delhi. He is internationally "
            "recognised for his work in movement disorders, Parkinson's disease, and deep brain "
            "stimulation patient selection."
        ),
        "medical_council_reg_no": "MCI-2002-DL-01988",
        "years_of_experience": 22,
        "consultation_fee_usd": "100.00",
        "consultation_duration_min": 45,
        "languages": "English, Telugu, Hindi",
        "hospital_affiliation": "Max Super Speciality Hospital, New Delhi",
        "timezone": "Asia/Kolkata",
        "specializations": ["Neurology", "Neurosurgery"],
        "education": [
            {"degree": "MBBS", "institution": "Osmania Medical College, Hyderabad", "year_completed": 1997},
            {"degree": "MD (Medicine)", "institution": "Nizam's Institute of Medical Sciences", "year_completed": 2000},
            {"degree": "DM (Neurology)", "institution": "AIIMS New Delhi", "year_completed": 2002},
            {"degree": "Fellowship (Movement Disorders)", "institution": "University College London, UK", "year_completed": 2004},
        ],
        "slots": [
            {"day": 1, "start": "09:00", "end": "12:00"},
            {"day": 3, "start": "09:00", "end": "12:00"},
            {"day": 5, "start": "09:00", "end": "11:00"},
        ],
    },
    # ── Oncology ───────────────────────────────────────────────────────────────
    {
        "email": "dr.roy@test.local",
        "first_name": "Sunita",
        "last_name": "Roy",
        "phone": "+91-9876543213",
        "bio": (
            "Dr. Sunita Roy is a medical oncologist at Tata Memorial Hospital, Mumbai, with 15 years "
            "of experience in breast, gynaecological, and haematological malignancies. She is a "
            "pioneer in metronomic chemotherapy protocols in India."
        ),
        "medical_council_reg_no": "MCI-2009-MH-06602",
        "years_of_experience": 15,
        "consultation_fee_usd": "90.00",
        "consultation_duration_min": 45,
        "languages": "English, Bengali, Hindi",
        "hospital_affiliation": "Tata Memorial Hospital, Mumbai",
        "timezone": "Asia/Kolkata",
        "specializations": ["Oncology"],
        "education": [
            {"degree": "MBBS", "institution": "Medical College Kolkata", "year_completed": 2003},
            {"degree": "MD (Medicine)", "institution": "PGI Chandigarh", "year_completed": 2006},
            {"degree": "DM (Medical Oncology)", "institution": "Tata Memorial Hospital, Mumbai", "year_completed": 2009},
        ],
        "slots": [
            {"day": 1, "start": "09:00", "end": "13:00"},
            {"day": 3, "start": "09:00", "end": "13:00"},
            {"day": 5, "start": "09:00", "end": "12:00"},
        ],
    },
    {
        "email": "dr.gupta@test.local",
        "first_name": "Ravi",
        "last_name": "Gupta",
        "phone": "+91-9876500104",
        "bio": (
            "Dr. Ravi Gupta is a surgical oncologist with 7 years of experience at Kokilaben "
            "Dhirubhai Ambani Hospital, Mumbai. He specialises in robotic-assisted cancer surgery "
            "for prostate, colorectal, and gynaecological cancers."
        ),
        "medical_council_reg_no": "MCI-2017-MH-22341",
        "years_of_experience": 7,
        "consultation_fee_usd": "65.00",
        "consultation_duration_min": 30,
        "languages": "English, Hindi, Marathi",
        "hospital_affiliation": "Kokilaben Dhirubhai Ambani Hospital, Mumbai",
        "timezone": "Asia/Kolkata",
        "specializations": ["Oncology"],
        "education": [
            {"degree": "MBBS", "institution": "Seth GS Medical College, Mumbai", "year_completed": 2012},
            {"degree": "MS (General Surgery)", "institution": "KEM Hospital, Mumbai", "year_completed": 2016},
            {"degree": "MCh (Surgical Oncology)", "institution": "Tata Memorial Hospital, Mumbai", "year_completed": 2019},
        ],
        "slots": [
            {"day": 0, "start": "10:00", "end": "14:00"},
            {"day": 2, "start": "10:00", "end": "14:00"},
            {"day": 4, "start": "10:00", "end": "14:00"},
        ],
    },
    # ── General Surgery ────────────────────────────────────────────────────────
    {
        "email": "dr.malhotra@test.local",
        "first_name": "Anil",
        "last_name": "Malhotra",
        "phone": "+91-9876500105",
        "bio": (
            "Dr. Anil Malhotra is a bariatric and metabolic surgeon with 9 years of experience "
            "at Medanta - The Medicity, Gurugram. He has performed over 1,200 bariatric procedures "
            "including sleeve gastrectomy, gastric bypass, and revisional bariatric surgery."
        ),
        "medical_council_reg_no": "MCI-2015-HR-19002",
        "years_of_experience": 9,
        "consultation_fee_usd": "60.00",
        "consultation_duration_min": 30,
        "languages": "English, Hindi, Punjabi",
        "hospital_affiliation": "Medanta - The Medicity, Gurugram",
        "timezone": "Asia/Kolkata",
        "specializations": ["General Surgery"],
        "education": [
            {"degree": "MBBS", "institution": "Maulana Azad Medical College, New Delhi", "year_completed": 2010},
            {"degree": "MS (General Surgery)", "institution": "AIIMS New Delhi", "year_completed": 2014},
            {"degree": "Fellowship in Bariatric Surgery", "institution": "Centre for Obesity & Diabetes Surgery, Sydney", "year_completed": 2016},
        ],
        "slots": [
            {"day": 0, "start": "09:00", "end": "13:00"},
            {"day": 2, "start": "09:00", "end": "13:00"},
            {"day": 4, "start": "14:00", "end": "17:00"},
        ],
    },
    {
        "email": "dr.pillai@test.local",
        "first_name": "Lakshmi",
        "last_name": "Pillai",
        "phone": "+91-9876500106",
        "bio": (
            "Dr. Lakshmi Pillai is a junior general surgeon with 2 years of post-residency "
            "experience at Apollo Hospitals, New Delhi. She has a keen interest in laparoscopic "
            "procedures and gastrointestinal surgery."
        ),
        "medical_council_reg_no": "MCI-2022-DL-33910",
        "years_of_experience": 2,
        "consultation_fee_usd": "40.00",
        "consultation_duration_min": 20,
        "languages": "English, Malayalam, Hindi",
        "hospital_affiliation": "Apollo Hospitals, New Delhi",
        "timezone": "Asia/Kolkata",
        "specializations": ["General Surgery"],
        "education": [
            {"degree": "MBBS", "institution": "Trivandrum Medical College", "year_completed": 2017},
            {"degree": "MS (General Surgery)", "institution": "Amrita Institute of Medical Sciences, Kochi", "year_completed": 2022},
        ],
        "slots": [
            {"day": 1, "start": "14:00", "end": "18:00"},
            {"day": 3, "start": "14:00", "end": "18:00"},
            {"day": 5, "start": "10:00", "end": "13:00"},
        ],
    },
    # ── Gastroenterology ───────────────────────────────────────────────────────
    {
        "email": "dr.joshi@test.local",
        "first_name": "Suresh",
        "last_name": "Joshi",
        "phone": "+91-9876500107",
        "bio": (
            "Dr. Suresh Joshi is a senior gastroenterologist and hepatologist with 14 years of "
            "experience at Medanta - The Medicity, Gurugram. He is an expert in advanced endoscopy, "
            "ERCP, liver diseases, and inflammatory bowel disease management."
        ),
        "medical_council_reg_no": "MCI-2010-HR-09821",
        "years_of_experience": 14,
        "consultation_fee_usd": "75.00",
        "consultation_duration_min": 30,
        "languages": "English, Hindi, Rajasthani",
        "hospital_affiliation": "Medanta - The Medicity, Gurugram",
        "timezone": "Asia/Kolkata",
        "specializations": ["Gastroenterology"],
        "education": [
            {"degree": "MBBS", "institution": "SMS Medical College, Jaipur", "year_completed": 2005},
            {"degree": "MD (Medicine)", "institution": "PGIMER, Chandigarh", "year_completed": 2008},
            {"degree": "DM (Gastroenterology)", "institution": "SGPGI, Lucknow", "year_completed": 2010},
        ],
        "slots": [
            {"day": 0, "start": "09:00", "end": "13:00"},
            {"day": 1, "start": "09:00", "end": "13:00"},
            {"day": 3, "start": "14:00", "end": "18:00"},
        ],
    },
    {
        "email": "dr.bose@test.local",
        "first_name": "Ananya",
        "last_name": "Bose",
        "phone": "+91-9876500108",
        "bio": (
            "Dr. Ananya Bose is a gastroenterologist with 4 years of experience at Yashoda "
            "Hospitals, Hyderabad. She specialises in diagnostic and therapeutic endoscopy, "
            "capsule endoscopy, and management of acute GI bleeding."
        ),
        "medical_council_reg_no": "MCI-2020-TS-29100",
        "years_of_experience": 4,
        "consultation_fee_usd": "50.00",
        "consultation_duration_min": 30,
        "languages": "English, Bengali, Telugu",
        "hospital_affiliation": "Yashoda Hospitals, Hyderabad",
        "timezone": "Asia/Kolkata",
        "specializations": ["Gastroenterology"],
        "education": [
            {"degree": "MBBS", "institution": "Calcutta Medical College", "year_completed": 2015},
            {"degree": "MD (General Medicine)", "institution": "IPGMER, Kolkata", "year_completed": 2019},
            {"degree": "Fellowship in Gastroenterology", "institution": "Asian Institute of Gastroenterology, Hyderabad", "year_completed": 2021},
        ],
        "slots": [
            {"day": 2, "start": "10:00", "end": "14:00"},
            {"day": 4, "start": "10:00", "end": "14:00"},
            {"day": 5, "start": "09:00", "end": "12:00"},
        ],
    },
    # ── Gynecology ─────────────────────────────────────────────────────────────
    {
        "email": "dr.mishra@test.local",
        "first_name": "Kavita",
        "last_name": "Mishra",
        "phone": "+91-9876500109",
        "bio": (
            "Dr. Kavita Mishra is a senior gynaecologist and laparoscopic surgeon with 17 years "
            "of experience at Kokilaben Dhirubhai Ambani Hospital, Mumbai. She specialises in "
            "minimally invasive hysterectomy, endometriosis, infertility surgery, and high-risk "
            "obstetric care."
        ),
        "medical_council_reg_no": "MCI-2007-MH-05511",
        "years_of_experience": 17,
        "consultation_fee_usd": "85.00",
        "consultation_duration_min": 45,
        "languages": "English, Hindi, Marathi",
        "hospital_affiliation": "Kokilaben Dhirubhai Ambani Hospital, Mumbai",
        "timezone": "Asia/Kolkata",
        "specializations": ["Gynecology"],
        "education": [
            {"degree": "MBBS", "institution": "BJ Medical College, Pune", "year_completed": 2002},
            {"degree": "MD (Obstetrics & Gynaecology)", "institution": "KEM Hospital, Mumbai", "year_completed": 2006},
            {"degree": "Fellowship in Laparoscopic Gynaecology", "institution": "Institut Mutualiste Montsouris, Paris", "year_completed": 2008},
        ],
        "slots": [
            {"day": 0, "start": "09:00", "end": "13:00"},
            {"day": 2, "start": "09:00", "end": "13:00"},
            {"day": 4, "start": "09:00", "end": "13:00"},
        ],
    },
    {
        "email": "dr.agarwal@test.local",
        "first_name": "Pooja",
        "last_name": "Agarwal",
        "phone": "+91-9876500110",
        "bio": (
            "Dr. Pooja Agarwal is a gynaecologist with 5 years of experience at Manipal Hospital, "
            "Bangalore. She has a special interest in reproductive medicine, PCOS management, "
            "colposcopy, and cervical cancer screening."
        ),
        "medical_council_reg_no": "MCI-2019-KA-28770",
        "years_of_experience": 5,
        "consultation_fee_usd": "55.00",
        "consultation_duration_min": 30,
        "languages": "English, Hindi, Kannada",
        "hospital_affiliation": "Manipal Hospital, Bangalore",
        "timezone": "Asia/Kolkata",
        "specializations": ["Gynecology"],
        "education": [
            {"degree": "MBBS", "institution": "Kasturba Medical College, Manipal", "year_completed": 2014},
            {"degree": "MS (Obstetrics & Gynaecology)", "institution": "Manipal Hospital, Bangalore", "year_completed": 2019},
        ],
        "slots": [
            {"day": 1, "start": "10:00", "end": "14:00"},
            {"day": 3, "start": "10:00", "end": "14:00"},
            {"day": 5, "start": "09:00", "end": "12:00"},
        ],
    },
    # ── Ophthalmology ──────────────────────────────────────────────────────────
    {
        "email": "dr.verma@test.local",
        "first_name": "Sanjay",
        "last_name": "Verma",
        "phone": "+91-9876500111",
        "bio": (
            "Dr. Sanjay Verma is an ophthalmologist with 10 years of experience at Yashoda "
            "Hospitals, Hyderabad. He specialises in refractive surgery, cataract surgery, "
            "retinal detachment repair, and vitreoretinal disorders."
        ),
        "medical_council_reg_no": "MCI-2014-TS-14900",
        "years_of_experience": 10,
        "consultation_fee_usd": "60.00",
        "consultation_duration_min": 20,
        "languages": "English, Hindi, Telugu",
        "hospital_affiliation": "Yashoda Hospitals, Hyderabad",
        "timezone": "Asia/Kolkata",
        "specializations": ["Ophthalmology"],
        "education": [
            {"degree": "MBBS", "institution": "Osmania Medical College, Hyderabad", "year_completed": 2009},
            {"degree": "MS (Ophthalmology)", "institution": "LV Prasad Eye Institute, Hyderabad", "year_completed": 2013},
            {"degree": "Fellowship in Vitreoretinal Surgery", "institution": "Sankara Nethralaya, Chennai", "year_completed": 2015},
        ],
        "slots": [
            {"day": 0, "start": "09:00", "end": "13:00"},
            {"day": 2, "start": "09:00", "end": "13:00"},
            {"day": 4, "start": "09:00", "end": "13:00"},
        ],
    },
    {
        "email": "dr.sinha@test.local",
        "first_name": "Preethi",
        "last_name": "Sinha",
        "phone": "+91-9876500112",
        "bio": (
            "Dr. Preethi Sinha is an ophthalmologist with 3 years of experience at Fortis "
            "Healthcare, Mumbai. She is passionate about corneal diseases, dry eye management, "
            "and paediatric ophthalmology."
        ),
        "medical_council_reg_no": "MCI-2021-MH-31200",
        "years_of_experience": 3,
        "consultation_fee_usd": "40.00",
        "consultation_duration_min": 20,
        "languages": "English, Tamil, Hindi",
        "hospital_affiliation": "Fortis Healthcare, Mumbai",
        "timezone": "Asia/Kolkata",
        "specializations": ["Ophthalmology"],
        "education": [
            {"degree": "MBBS", "institution": "Sri Ramachandra Medical College, Chennai", "year_completed": 2015},
            {"degree": "MS (Ophthalmology)", "institution": "Aravind Eye Hospital, Madurai", "year_completed": 2021},
        ],
        "slots": [
            {"day": 1, "start": "11:00", "end": "15:00"},
            {"day": 3, "start": "11:00", "end": "15:00"},
            {"day": 5, "start": "10:00", "end": "13:00"},
        ],
    },
    # ── Pulmonology ────────────────────────────────────────────────────────────
    {
        "email": "dr.reddy@test.local",
        "first_name": "Suresh",
        "last_name": "Reddy",
        "phone": "+91-9876500113",
        "bio": (
            "Dr. Suresh Reddy is a pulmonologist and critical care specialist with 15 years of "
            "experience at Yashoda Hospitals, Hyderabad. He is an expert in bronchoscopy, "
            "interventional pulmonology, VATS procedures, and lung transplant workup."
        ),
        "medical_council_reg_no": "MCI-2009-TS-07700",
        "years_of_experience": 15,
        "consultation_fee_usd": "70.00",
        "consultation_duration_min": 30,
        "languages": "English, Telugu, Hindi",
        "hospital_affiliation": "Yashoda Hospitals, Hyderabad",
        "timezone": "Asia/Kolkata",
        "specializations": ["Pulmonology"],
        "education": [
            {"degree": "MBBS", "institution": "Andhra Medical College, Visakhapatnam", "year_completed": 2004},
            {"degree": "MD (Respiratory Medicine)", "institution": "Nizam's Institute of Medical Sciences, Hyderabad", "year_completed": 2007},
            {"degree": "Fellowship in Interventional Pulmonology", "institution": "Cleveland Clinic, USA", "year_completed": 2010},
        ],
        "slots": [
            {"day": 0, "start": "09:00", "end": "12:00"},
            {"day": 2, "start": "09:00", "end": "12:00"},
            {"day": 4, "start": "14:00", "end": "17:00"},
        ],
    },
    {
        "email": "dr.iyer@test.local",
        "first_name": "Meera",
        "last_name": "Iyer",
        "phone": "+91-9876500114",
        "bio": (
            "Dr. Meera Iyer is a pulmonologist with 6 years of experience at Manipal Hospital, "
            "Bangalore. She specialises in asthma, COPD, interstitial lung disease, and "
            "sleep-disordered breathing."
        ),
        "medical_council_reg_no": "MCI-2018-KA-25600",
        "years_of_experience": 6,
        "consultation_fee_usd": "55.00",
        "consultation_duration_min": 30,
        "languages": "English, Tamil, Kannada",
        "hospital_affiliation": "Manipal Hospital, Bangalore",
        "timezone": "Asia/Kolkata",
        "specializations": ["Pulmonology"],
        "education": [
            {"degree": "MBBS", "institution": "Madras Medical College, Chennai", "year_completed": 2013},
            {"degree": "MD (Respiratory Medicine)", "institution": "Sri Ramachandra University, Chennai", "year_completed": 2018},
        ],
        "slots": [
            {"day": 1, "start": "09:00", "end": "13:00"},
            {"day": 3, "start": "09:00", "end": "13:00"},
            {"day": 5, "start": "09:00", "end": "11:00"},
        ],
    },
    # ── Urology ────────────────────────────────────────────────────────────────
    {
        "email": "dr.pandey@test.local",
        "first_name": "Vivek",
        "last_name": "Pandey",
        "phone": "+91-9876500115",
        "bio": (
            "Dr. Vivek Pandey is a urologist with 12 years of experience at Kokilaben Dhirubhai "
            "Ambani Hospital, Mumbai. He specialises in robotic urology, uro-oncology, kidney "
            "stone management (PCNL, RIRS), and BPH treatment."
        ),
        "medical_council_reg_no": "MCI-2012-MH-10440",
        "years_of_experience": 12,
        "consultation_fee_usd": "75.00",
        "consultation_duration_min": 30,
        "languages": "English, Hindi, Marathi",
        "hospital_affiliation": "Kokilaben Dhirubhai Ambani Hospital, Mumbai",
        "timezone": "Asia/Kolkata",
        "specializations": ["Urology"],
        "education": [
            {"degree": "MBBS", "institution": "Grant Medical College, Mumbai", "year_completed": 2006},
            {"degree": "MS (General Surgery)", "institution": "Seth GS Medical College, Mumbai", "year_completed": 2010},
            {"degree": "MCh (Urology)", "institution": "PGI Chandigarh", "year_completed": 2013},
        ],
        "slots": [
            {"day": 0, "start": "10:00", "end": "14:00"},
            {"day": 2, "start": "10:00", "end": "14:00"},
            {"day": 4, "start": "10:00", "end": "14:00"},
        ],
    },
    {
        "email": "dr.chandra@test.local",
        "first_name": "Geeta",
        "last_name": "Chandra",
        "phone": "+91-9876500116",
        "bio": (
            "Dr. Geeta Chandra is a urologist with 4 years of experience at Yashoda Hospitals, "
            "Hyderabad. She focuses on female urology, overactive bladder, urinary incontinence, "
            "and minimally invasive stone surgery."
        ),
        "medical_council_reg_no": "MCI-2020-TS-29500",
        "years_of_experience": 4,
        "consultation_fee_usd": "50.00",
        "consultation_duration_min": 30,
        "languages": "English, Telugu, Hindi",
        "hospital_affiliation": "Yashoda Hospitals, Hyderabad",
        "timezone": "Asia/Kolkata",
        "specializations": ["Urology"],
        "education": [
            {"degree": "MBBS", "institution": "Gandhi Medical College, Hyderabad", "year_completed": 2014},
            {"degree": "MS (General Surgery)", "institution": "Osmania Medical College, Hyderabad", "year_completed": 2018},
            {"degree": "MCh (Urology)", "institution": "Nizam's Institute of Medical Sciences", "year_completed": 2022},
        ],
        "slots": [
            {"day": 1, "start": "10:00", "end": "14:00"},
            {"day": 3, "start": "10:00", "end": "14:00"},
            {"day": 5, "start": "09:00", "end": "12:00"},
        ],
    },
    # ── ENT Surgery ────────────────────────────────────────────────────────────
    {
        "email": "dr.saxena@test.local",
        "first_name": "Rohit",
        "last_name": "Saxena",
        "phone": "+91-9876500117",
        "bio": (
            "Dr. Rohit Saxena is a senior ENT surgeon with 11 years of experience at Max Super "
            "Speciality Hospital, New Delhi. He is an expert in cochlear implantation, skull base "
            "surgery, functional endoscopic sinus surgery, and head & neck tumours."
        ),
        "medical_council_reg_no": "MCI-2013-DL-12800",
        "years_of_experience": 11,
        "consultation_fee_usd": "65.00",
        "consultation_duration_min": 30,
        "languages": "English, Hindi",
        "hospital_affiliation": "Max Super Speciality Hospital, New Delhi",
        "timezone": "Asia/Kolkata",
        "specializations": ["ENT Surgery"],
        "education": [
            {"degree": "MBBS", "institution": "Lady Hardinge Medical College, New Delhi", "year_completed": 2007},
            {"degree": "MS (ENT)", "institution": "AIIMS New Delhi", "year_completed": 2011},
            {"degree": "Fellowship in Otology & Cochlear Implants", "institution": "University of Melbourne, Australia", "year_completed": 2014},
        ],
        "slots": [
            {"day": 0, "start": "09:00", "end": "13:00"},
            {"day": 2, "start": "09:00", "end": "13:00"},
            {"day": 4, "start": "09:00", "end": "13:00"},
        ],
    },
    {
        "email": "dr.desai@test.local",
        "first_name": "Nandita",
        "last_name": "Desai",
        "phone": "+91-9876500118",
        "bio": (
            "Dr. Nandita Desai is an ENT surgeon with 4 years of experience at Yashoda Hospitals, "
            "Hyderabad. She specialises in voice disorders, thyroid surgery, tonsillectomy, "
            "and paediatric ENT conditions."
        ),
        "medical_council_reg_no": "MCI-2020-TS-30100",
        "years_of_experience": 4,
        "consultation_fee_usd": "45.00",
        "consultation_duration_min": 20,
        "languages": "English, Gujarati, Hindi, Telugu",
        "hospital_affiliation": "Yashoda Hospitals, Hyderabad",
        "timezone": "Asia/Kolkata",
        "specializations": ["ENT Surgery"],
        "education": [
            {"degree": "MBBS", "institution": "Government Medical College, Surat", "year_completed": 2014},
            {"degree": "MS (ENT)", "institution": "BJ Medical College, Ahmedabad", "year_completed": 2019},
        ],
        "slots": [
            {"day": 1, "start": "11:00", "end": "15:00"},
            {"day": 3, "start": "11:00", "end": "15:00"},
            {"day": 5, "start": "10:00", "end": "13:00"},
        ],
    },
    # ── Neurosurgery ───────────────────────────────────────────────────────────
    {
        "email": "dr.chatterjee@test.local",
        "first_name": "Biplab",
        "last_name": "Chatterjee",
        "phone": "+91-9876500119",
        "bio": (
            "Dr. Biplab Chatterjee is a neurosurgeon with 13 years of experience at Max Super "
            "Speciality Hospital, New Delhi. He specialises in brain tumour surgery, cerebrovascular "
            "surgery, deep brain stimulation, and minimally invasive spine neurosurgery."
        ),
        "medical_council_reg_no": "MCI-2011-DL-10200",
        "years_of_experience": 13,
        "consultation_fee_usd": "90.00",
        "consultation_duration_min": 45,
        "languages": "English, Bengali, Hindi",
        "hospital_affiliation": "Max Super Speciality Hospital, New Delhi",
        "timezone": "Asia/Kolkata",
        "specializations": ["Neurosurgery"],
        "education": [
            {"degree": "MBBS", "institution": "RG Kar Medical College, Kolkata", "year_completed": 2005},
            {"degree": "MS (General Surgery)", "institution": "IPGMER, Kolkata", "year_completed": 2008},
            {"degree": "MCh (Neurosurgery)", "institution": "AIIMS New Delhi", "year_completed": 2012},
        ],
        "slots": [
            {"day": 0, "start": "09:00", "end": "12:00"},
            {"day": 2, "start": "09:00", "end": "12:00"},
            {"day": 4, "start": "14:00", "end": "17:00"},
        ],
    },
    {
        "email": "dr.tiwari@test.local",
        "first_name": "Shalini",
        "last_name": "Tiwari",
        "phone": "+91-9876500120",
        "bio": (
            "Dr. Shalini Tiwari is a neurosurgeon with 5 years of experience at Manipal Hospital, "
            "Bangalore. She focuses on neuro-oncology surgery, endoscopic brain surgery, and "
            "spinal cord tumour removal."
        ),
        "medical_council_reg_no": "MCI-2019-KA-27500",
        "years_of_experience": 5,
        "consultation_fee_usd": "65.00",
        "consultation_duration_min": 30,
        "languages": "English, Hindi, Kannada",
        "hospital_affiliation": "Manipal Hospital, Bangalore",
        "timezone": "Asia/Kolkata",
        "specializations": ["Neurosurgery"],
        "education": [
            {"degree": "MBBS", "institution": "Bangalore Medical College", "year_completed": 2012},
            {"degree": "MS (General Surgery)", "institution": "St. John's Medical College, Bangalore", "year_completed": 2015},
            {"degree": "MCh (Neurosurgery)", "institution": "NIMHANS, Bangalore", "year_completed": 2020},
        ],
        "slots": [
            {"day": 1, "start": "09:00", "end": "13:00"},
            {"day": 3, "start": "09:00", "end": "13:00"},
            {"day": 5, "start": "09:00", "end": "12:00"},
        ],
    },
]

HOSPITALS = [
    # ── Apollo Hospitals, New Delhi ────────────────────────────────────────────
    {
        "name": "Apollo Hospitals",
        "city": "New Delhi",
        "state": "Delhi",
        "description": (
            "Apollo Hospitals New Delhi is a 710-bed tertiary care facility and one of India's "
            "most trusted multi-speciality hospitals. Accredited by JCI and NABH, it offers "
            "advanced cardiac, oncology, neurosciences, and transplant programmes."
        ),
        "accreditations": "JCI, NABH, NABL",
        "website": "https://www.apollohospitals.com",
        "is_partner": True,
        "packages": [
            {
                "name": "Coronary Artery Bypass Graft (CABG)",
                "surgery_type": "Cardiac Surgery",
                "description": "Full-package open-heart bypass surgery including pre-op cardiac workup, ICU care, 7-night hospital stay, physiotherapy, and 7-night hotel recovery.",
                "total_duration_days": 21,
                "hospital_stay_days": 10,
                "recovery_stay_days": 11,
                "price_usd": "7500.00",
                "includes_flight": True,
                "flight_class": "economy",
                "includes_visa_assistance": True,
                "includes_accommodation": True,
                "accommodation_type": "hotel_4star",
                "includes_transport": True,
                "includes_meals": True,
                "inclusions_text": (
                    "Round-trip economy flights\n"
                    "Airport pickup and drop\n"
                    "10 nights hospital accommodation\n"
                    "7 nights 4-star hotel recovery stay\n"
                    "All meals during hospital stay\n"
                    "Pre-op tests (ECG, echo, blood panel)\n"
                    "Surgeon and anaesthetist fees\n"
                    "ICU and post-op monitoring\n"
                    "Cardiac rehabilitation sessions\n"
                    "Visa invitation letter\n"
                    "Dedicated patient coordinator"
                ),
                "exclusions_text": (
                    "Travel insurance\n"
                    "Personal expenses\n"
                    "Medications after discharge\n"
                    "Additional nights if complications arise"
                ),
                "is_active": True,
            },
            {
                "name": "Total Knee Replacement",
                "surgery_type": "Orthopedic Surgery",
                "description": "Bilateral or unilateral total knee replacement with imported implant, physiotherapy programme, and hotel recovery.",
                "total_duration_days": 18,
                "hospital_stay_days": 7,
                "recovery_stay_days": 11,
                "price_usd": "5800.00",
                "includes_flight": True,
                "flight_class": "economy",
                "includes_visa_assistance": True,
                "includes_accommodation": True,
                "accommodation_type": "hotel_3star",
                "includes_transport": True,
                "includes_meals": False,
                "inclusions_text": (
                    "Round-trip economy flights\n"
                    "Airport pickup and drop\n"
                    "7 nights hospital stay\n"
                    "11 nights 3-star hotel recovery\n"
                    "Imported knee implant (Zimmer Biomet)\n"
                    "Pre-op X-rays and blood tests\n"
                    "Physiotherapy (10 sessions)\n"
                    "Visa invitation letter"
                ),
                "exclusions_text": (
                    "Meals at hotel\n"
                    "Travel insurance\n"
                    "Personal expenses"
                ),
                "is_active": True,
            },
            {
                "name": "Laparoscopic Gastric Bypass Surgery",
                "surgery_type": "Bariatric Surgery",
                "description": "Minimally invasive Roux-en-Y gastric bypass for morbid obesity (BMI ≥ 40 or BMI ≥ 35 with comorbidities). Includes nutritional counselling and follow-up.",
                "total_duration_days": 14,
                "hospital_stay_days": 5,
                "recovery_stay_days": 9,
                "price_usd": "5200.00",
                "includes_flight": True,
                "flight_class": "economy",
                "includes_visa_assistance": True,
                "includes_accommodation": True,
                "accommodation_type": "hotel_3star",
                "includes_transport": True,
                "includes_meals": True,
                "inclusions_text": (
                    "Round-trip economy flights\n"
                    "Airport pickup and drop\n"
                    "5 nights hospital stay\n"
                    "9 nights 3-star hotel\n"
                    "Hospital meals (liquid diet post-op)\n"
                    "Pre-op metabolic workup\n"
                    "Surgeon, anaesthetist, OT fees\n"
                    "Bariatric dietitian consultations (3 sessions)\n"
                    "Visa invitation letter"
                ),
                "exclusions_text": (
                    "Hotel meals\n"
                    "Long-term supplements\n"
                    "Travel insurance\n"
                    "Personal expenses"
                ),
                "is_active": True,
            },
            {
                "name": "Lung Cancer Surgical Package (Lobectomy)",
                "surgery_type": "Oncology Surgery",
                "description": "VATS or open lobectomy for non-small cell lung cancer with staging PET-CT, mediastinoscopy if required, and post-op respiratory physiotherapy.",
                "total_duration_days": 22,
                "hospital_stay_days": 10,
                "recovery_stay_days": 12,
                "price_usd": "9800.00",
                "includes_flight": True,
                "flight_class": "business",
                "includes_visa_assistance": True,
                "includes_accommodation": True,
                "accommodation_type": "hotel_4star",
                "includes_transport": True,
                "includes_meals": True,
                "inclusions_text": (
                    "Round-trip business class flights\n"
                    "Airport pickup and drop\n"
                    "10 nights hospital stay\n"
                    "12 nights 4-star hotel for companion\n"
                    "All hospital meals\n"
                    "PET-CT scan, bronchoscopy\n"
                    "Thoracic surgeon + oncologist fees\n"
                    "Post-op chest physiotherapy\n"
                    "Oncology MDT report\n"
                    "Visa invitation for patient + companion"
                ),
                "exclusions_text": (
                    "Chemotherapy or radiation post-surgery\n"
                    "Travel insurance\n"
                    "Personal expenses"
                ),
                "is_active": True,
            },
        ],
    },
    # ── Fortis Healthcare, Mumbai ──────────────────────────────────────────────
    {
        "name": "Fortis Healthcare",
        "city": "Mumbai",
        "state": "Maharashtra",
        "description": (
            "Fortis Healthcare Mumbai is a 312-bed JCI-accredited hospital renowned for its "
            "orthopaedic, cardiac, and neurosciences departments. It is one of Western India's "
            "leading centres for robotic surgery and sports medicine."
        ),
        "accreditations": "JCI, NABH",
        "website": "https://www.fortishealthcare.com",
        "is_partner": True,
        "packages": [
            {
                "name": "Hip Resurfacing Surgery",
                "surgery_type": "Orthopedic Surgery",
                "description": "Minimally invasive hip resurfacing using Birmingham Hip Resurfacing (BHR) system, ideal for active patients under 65.",
                "total_duration_days": 16,
                "hospital_stay_days": 6,
                "recovery_stay_days": 10,
                "price_usd": "6200.00",
                "includes_flight": True,
                "flight_class": "economy",
                "includes_visa_assistance": True,
                "includes_accommodation": True,
                "accommodation_type": "hotel_4star",
                "includes_transport": True,
                "includes_meals": True,
                "inclusions_text": (
                    "Round-trip economy flights\n"
                    "Airport transfers\n"
                    "6 nights hospital stay\n"
                    "10 nights 4-star hotel\n"
                    "All hospital meals\n"
                    "BHR implant\n"
                    "Pre-op MRI and blood panel\n"
                    "Post-op physiotherapy (8 sessions)\n"
                    "Visa support letter"
                ),
                "exclusions_text": (
                    "Hotel meals\n"
                    "Travel insurance\n"
                    "Personal shopping"
                ),
                "is_active": True,
            },
            {
                "name": "Spinal Fusion Surgery",
                "surgery_type": "Spine Surgery",
                "description": "Lumbar or cervical spinal fusion for degenerative disc disease, spondylolisthesis, or herniated disc with nerve compression.",
                "total_duration_days": 20,
                "hospital_stay_days": 8,
                "recovery_stay_days": 12,
                "price_usd": "6900.00",
                "includes_flight": False,
                "flight_class": "economy",
                "includes_visa_assistance": True,
                "includes_accommodation": True,
                "accommodation_type": "serviced_apt",
                "includes_transport": True,
                "includes_meals": False,
                "inclusions_text": (
                    "8 nights hospital stay\n"
                    "12 nights serviced apartment\n"
                    "Airport transfers\n"
                    "Pre-op MRI and nerve conduction study\n"
                    "Titanium cage implant and pedicle screws\n"
                    "Physiotherapy programme (12 sessions)\n"
                    "Brace/support belt\n"
                    "Visa invitation letter"
                ),
                "exclusions_text": (
                    "International flights\n"
                    "Meals\n"
                    "Travel insurance"
                ),
                "is_active": True,
            },
            {
                "name": "Robotic Total Hip Replacement",
                "surgery_type": "Orthopedic Surgery",
                "description": "Mako robotic-arm assisted total hip replacement offering superior implant positioning and faster recovery compared to conventional THA.",
                "total_duration_days": 15,
                "hospital_stay_days": 5,
                "recovery_stay_days": 10,
                "price_usd": "7100.00",
                "includes_flight": True,
                "flight_class": "economy",
                "includes_visa_assistance": True,
                "includes_accommodation": True,
                "accommodation_type": "hotel_4star",
                "includes_transport": True,
                "includes_meals": True,
                "inclusions_text": (
                    "Round-trip economy flights\n"
                    "Airport pickup and drop\n"
                    "5 nights hospital stay\n"
                    "10 nights 4-star hotel recovery\n"
                    "All hospital meals\n"
                    "Mako robotic procedure fee\n"
                    "Cementless hip implant (Stryker)\n"
                    "Pre-op CT for robotic planning\n"
                    "Physiotherapy (10 sessions)\n"
                    "Visa invitation letter"
                ),
                "exclusions_text": (
                    "Hotel meals\n"
                    "Travel insurance\n"
                    "Personal expenses"
                ),
                "is_active": True,
            },
            {
                "name": "Deep Brain Stimulation (DBS) for Parkinson's",
                "surgery_type": "Neurosurgery",
                "description": "Bilateral subthalamic nucleus DBS for advanced Parkinson's disease with pre-op neuropsychological evaluation, implant surgery, and programming sessions.",
                "total_duration_days": 28,
                "hospital_stay_days": 12,
                "recovery_stay_days": 16,
                "price_usd": "18500.00",
                "includes_flight": True,
                "flight_class": "business",
                "includes_visa_assistance": True,
                "includes_accommodation": True,
                "accommodation_type": "hotel_4star",
                "includes_transport": True,
                "includes_meals": True,
                "inclusions_text": (
                    "Round-trip business class flights\n"
                    "Airport pickup and drop\n"
                    "12 nights hospital stay\n"
                    "16 nights 4-star hotel for patient + companion\n"
                    "All hospital meals\n"
                    "DBS system (Medtronic or Abbott)\n"
                    "Neurosurgeon + neurologist fees\n"
                    "Intraoperative neurophysiology monitoring\n"
                    "3 DBS programming sessions post-implant\n"
                    "Physiotherapy and occupational therapy\n"
                    "Visa invitation for patient + companion"
                ),
                "exclusions_text": (
                    "Long-term DBS battery replacement\n"
                    "Travel insurance\n"
                    "Personal expenses"
                ),
                "is_active": True,
            },
        ],
    },
    # ── Manipal Hospital, Bangalore ────────────────────────────────────────────
    {
        "name": "Manipal Hospital",
        "city": "Bangalore",
        "state": "Karnataka",
        "description": (
            "Manipal Hospital Bangalore is a 650-bed NABH-accredited tertiary referral centre "
            "known for its neurosciences, oncology, and solid organ transplant programmes. "
            "It operates a 24/7 comprehensive stroke centre."
        ),
        "accreditations": "NABH, NABL",
        "website": "https://www.manipalhospitals.com",
        "is_partner": True,
        "packages": [
            {
                "name": "Craniotomy for Brain Tumour",
                "surgery_type": "Neurosurgery",
                "description": "Awake or standard craniotomy with intraoperative neuromonitoring for benign or malignant brain tumours, including post-op ICU and rehabilitation.",
                "total_duration_days": 25,
                "hospital_stay_days": 14,
                "recovery_stay_days": 11,
                "price_usd": "9500.00",
                "includes_flight": True,
                "flight_class": "business",
                "includes_visa_assistance": True,
                "includes_accommodation": True,
                "accommodation_type": "hotel_4star",
                "includes_transport": True,
                "includes_meals": True,
                "inclusions_text": (
                    "Round-trip business class flights\n"
                    "Airport pickup and drop\n"
                    "14 nights hospital stay (includes ICU)\n"
                    "11 nights 4-star hotel for companion\n"
                    "All hospital meals for patient\n"
                    "Meals for one companion during hospital stay\n"
                    "Pre-op MRI brain with contrast, biopsy if needed\n"
                    "Intraoperative neurophysiological monitoring\n"
                    "Post-op speech and physiotherapy\n"
                    "Visa invitation letter for patient + companion"
                ),
                "exclusions_text": (
                    "Radiation or chemotherapy after surgery\n"
                    "Travel insurance\n"
                    "Personal expenses"
                ),
                "is_active": True,
            },
            {
                "name": "Liver Transplant Evaluation Package",
                "surgery_type": "Transplant Surgery",
                "description": "Comprehensive liver transplant evaluation with MELD scoring, imaging, and transplant team consultation. Does not include the transplant surgery itself.",
                "total_duration_days": 10,
                "hospital_stay_days": 3,
                "recovery_stay_days": 7,
                "price_usd": "2800.00",
                "includes_flight": False,
                "flight_class": "economy",
                "includes_visa_assistance": True,
                "includes_accommodation": True,
                "accommodation_type": "hotel_3star",
                "includes_transport": True,
                "includes_meals": False,
                "inclusions_text": (
                    "3 nights hospital stay\n"
                    "7 nights 3-star hotel\n"
                    "Airport transfers\n"
                    "Full liver transplant workup (MRI, CT, biopsy)\n"
                    "MELD/PELD scoring\n"
                    "Transplant team consultation\n"
                    "Dietary counselling\n"
                    "Visa support letter"
                ),
                "exclusions_text": (
                    "International flights\n"
                    "Meals\n"
                    "Actual transplant surgery cost\n"
                    "Travel insurance"
                ),
                "is_active": True,
            },
            {
                "name": "Liver Resection for HCC",
                "surgery_type": "Gastroenterology Surgery",
                "description": "Laparoscopic or open hepatectomy for hepatocellular carcinoma (HCC) or liver metastases with pre-op volumetric CT and multidisciplinary oncology review.",
                "total_duration_days": 20,
                "hospital_stay_days": 9,
                "recovery_stay_days": 11,
                "price_usd": "8200.00",
                "includes_flight": True,
                "flight_class": "economy",
                "includes_visa_assistance": True,
                "includes_accommodation": True,
                "accommodation_type": "hotel_4star",
                "includes_transport": True,
                "includes_meals": True,
                "inclusions_text": (
                    "Round-trip economy flights\n"
                    "Airport transfers\n"
                    "9 nights hospital stay\n"
                    "11 nights 4-star hotel\n"
                    "All hospital meals\n"
                    "Pre-op liver MRI + volumetry CT\n"
                    "Hepato-biliary surgeon fees\n"
                    "ICU monitoring\n"
                    "Post-op dietary counselling\n"
                    "Visa invitation letter"
                ),
                "exclusions_text": (
                    "Chemotherapy or TACE after surgery\n"
                    "Travel insurance\n"
                    "Personal expenses"
                ),
                "is_active": True,
            },
            {
                "name": "Robotic Hysterectomy",
                "surgery_type": "Gynecology Surgery",
                "description": "Da Vinci robotic-assisted total or radical hysterectomy for fibroids, endometriosis, or early-stage cervical/endometrial cancer.",
                "total_duration_days": 12,
                "hospital_stay_days": 4,
                "recovery_stay_days": 8,
                "price_usd": "4500.00",
                "includes_flight": True,
                "flight_class": "economy",
                "includes_visa_assistance": True,
                "includes_accommodation": True,
                "accommodation_type": "hotel_3star",
                "includes_transport": True,
                "includes_meals": True,
                "inclusions_text": (
                    "Round-trip economy flights\n"
                    "Airport pickup and drop\n"
                    "4 nights hospital stay\n"
                    "8 nights 3-star hotel recovery\n"
                    "All hospital meals\n"
                    "Robotic procedure (Da Vinci) fee\n"
                    "Gynaecologist and anaesthetist fees\n"
                    "Pre-op ultrasound + blood panel\n"
                    "Visa invitation letter"
                ),
                "exclusions_text": (
                    "Hotel meals\n"
                    "Travel insurance\n"
                    "Personal expenses"
                ),
                "is_active": True,
            },
        ],
    },
    # ── Narayana Health, Bangalore ─────────────────────────────────────────────
    {
        "name": "Narayana Health",
        "city": "Bangalore",
        "state": "Karnataka",
        "description": (
            "Narayana Health Bangalore is one of India's largest cardiac surgery centres, "
            "performing over 30 open-heart surgeries daily at globally competitive prices. "
            "NABH and JCI accredited, it is a pioneer in affordable high-volume cardiac care, "
            "orthopaedics, and solid organ transplantation."
        ),
        "accreditations": "JCI, NABH",
        "website": "https://www.narayanahealth.org",
        "is_partner": True,
        "packages": [
            {
                "name": "Beating Heart CABG (Off-Pump)",
                "surgery_type": "Cardiac Surgery",
                "description": "Off-pump coronary artery bypass graft (beating heart surgery) — avoids cardiopulmonary bypass, reducing stroke risk and recovery time. Ideal for high-risk patients.",
                "total_duration_days": 18,
                "hospital_stay_days": 8,
                "recovery_stay_days": 10,
                "price_usd": "6200.00",
                "includes_flight": True,
                "flight_class": "economy",
                "includes_visa_assistance": True,
                "includes_accommodation": True,
                "accommodation_type": "hotel_3star",
                "includes_transport": True,
                "includes_meals": True,
                "inclusions_text": (
                    "Round-trip economy flights\n"
                    "Airport pickup and drop\n"
                    "8 nights hospital stay\n"
                    "10 nights 3-star hotel recovery\n"
                    "All hospital meals\n"
                    "Pre-op cardiac evaluation (ECG, echo, angio review)\n"
                    "Surgeon, perfusionist, and anaesthetist fees\n"
                    "ICU and step-down care\n"
                    "Cardiac rehabilitation (6 sessions)\n"
                    "Visa invitation letter\n"
                    "Dedicated international patient desk"
                ),
                "exclusions_text": (
                    "Travel insurance\n"
                    "Personal expenses\n"
                    "Post-discharge medications\n"
                    "Additional ICU days if complications arise"
                ),
                "is_active": True,
            },
            {
                "name": "Total Knee Replacement — Narayana Health",
                "surgery_type": "Orthopedic Surgery",
                "description": "Unilateral or bilateral total knee replacement with high-flexion implant options. Narayana Health's volume-driven model provides excellent outcomes at a lower cost.",
                "total_duration_days": 16,
                "hospital_stay_days": 6,
                "recovery_stay_days": 10,
                "price_usd": "4800.00",
                "includes_flight": True,
                "flight_class": "economy",
                "includes_visa_assistance": True,
                "includes_accommodation": True,
                "accommodation_type": "hotel_3star",
                "includes_transport": True,
                "includes_meals": False,
                "inclusions_text": (
                    "Round-trip economy flights\n"
                    "Airport transfers\n"
                    "6 nights hospital stay\n"
                    "10 nights 3-star hotel recovery\n"
                    "Knee implant (DePuy Synthes or equivalent)\n"
                    "Pre-op X-rays and blood panel\n"
                    "Physiotherapy (8 sessions)\n"
                    "Visa invitation letter"
                ),
                "exclusions_text": (
                    "Hotel meals\n"
                    "Travel insurance\n"
                    "Personal expenses"
                ),
                "is_active": True,
            },
            {
                "name": "Kidney Transplant Package",
                "surgery_type": "Transplant Surgery",
                "description": "Living-donor kidney transplant including recipient workup, donor evaluation, surgery, and 3-month post-transplant monitoring protocol.",
                "total_duration_days": 35,
                "hospital_stay_days": 15,
                "recovery_stay_days": 20,
                "price_usd": "13500.00",
                "includes_flight": False,
                "flight_class": "economy",
                "includes_visa_assistance": True,
                "includes_accommodation": True,
                "accommodation_type": "serviced_apt",
                "includes_transport": True,
                "includes_meals": False,
                "inclusions_text": (
                    "15 nights hospital stay (recipient + donor)\n"
                    "20 nights serviced apartment (near hospital)\n"
                    "Airport transfers\n"
                    "Full recipient and donor workup\n"
                    "Transplant surgeon, nephrologist, anaesthetist fees\n"
                    "Immunosuppressant medications for first month\n"
                    "Post-op renal function monitoring (weekly)\n"
                    "Visa invitation letter for patient + donor"
                ),
                "exclusions_text": (
                    "International flights\n"
                    "Long-term immunosuppressants (beyond 1 month)\n"
                    "Travel insurance\n"
                    "Personal expenses"
                ),
                "is_active": True,
            },
            {
                "name": "Paediatric Cardiac Surgery (VSD / ASD Repair)",
                "surgery_type": "Cardiac Surgery",
                "description": "Open-heart repair of congenital septal defects (VSD or ASD) in children, with dedicated paediatric cardiac ICU and family accommodation.",
                "total_duration_days": 20,
                "hospital_stay_days": 10,
                "recovery_stay_days": 10,
                "price_usd": "5500.00",
                "includes_flight": True,
                "flight_class": "economy",
                "includes_visa_assistance": True,
                "includes_accommodation": True,
                "accommodation_type": "hotel_3star",
                "includes_transport": True,
                "includes_meals": True,
                "inclusions_text": (
                    "Round-trip economy flights (child + 1 parent)\n"
                    "Airport pickup and drop\n"
                    "10 nights paediatric cardiac unit\n"
                    "10 nights hotel for parents\n"
                    "All hospital meals for child + 1 parent\n"
                    "Paediatric cardiac surgeon + anaesthetist\n"
                    "Paediatric cardiac ICU care\n"
                    "Echocardiogram follow-up before discharge\n"
                    "Visa invitation for child + parents"
                ),
                "exclusions_text": (
                    "Travel insurance\n"
                    "Personal expenses\n"
                    "Medications after discharge"
                ),
                "is_active": True,
            },
        ],
    },
    # ── Max Super Speciality Hospital, New Delhi ───────────────────────────────
    {
        "name": "Max Super Speciality Hospital",
        "city": "New Delhi",
        "state": "Delhi",
        "description": (
            "Max Super Speciality Hospital Saket, New Delhi is a 500-bed quaternary care hospital "
            "and one of North India's leading centres for cardiac sciences, cancer care, "
            "neurosciences, and transplant surgery. It holds JCI and NABH accreditation."
        ),
        "accreditations": "JCI, NABH, NABL",
        "website": "https://www.maxhealthcare.in",
        "is_partner": True,
        "packages": [
            {
                "name": "Valve Replacement Surgery (Aortic / Mitral)",
                "surgery_type": "Cardiac Surgery",
                "description": "Surgical aortic or mitral valve replacement using biological (tissue) or mechanical prosthesis, with pre-op cardiac catheterisation and post-op rehabilitation.",
                "total_duration_days": 22,
                "hospital_stay_days": 10,
                "recovery_stay_days": 12,
                "price_usd": "8500.00",
                "includes_flight": True,
                "flight_class": "economy",
                "includes_visa_assistance": True,
                "includes_accommodation": True,
                "accommodation_type": "hotel_4star",
                "includes_transport": True,
                "includes_meals": True,
                "inclusions_text": (
                    "Round-trip economy flights\n"
                    "Airport pickup and drop\n"
                    "10 nights hospital stay (incl. ICU)\n"
                    "12 nights 4-star hotel recovery\n"
                    "All hospital meals\n"
                    "Pre-op cardiac catheterisation\n"
                    "Valve prosthesis (biological or mechanical)\n"
                    "Cardiothoracic surgeon + perfusionist fees\n"
                    "ICU and telemetry monitoring\n"
                    "Cardiac rehabilitation (8 sessions)\n"
                    "Visa invitation letter"
                ),
                "exclusions_text": (
                    "Long-term anticoagulant medications\n"
                    "Travel insurance\n"
                    "Personal expenses"
                ),
                "is_active": True,
            },
            {
                "name": "Breast Cancer Surgery & Reconstruction",
                "surgery_type": "Oncology Surgery",
                "description": "Mastectomy (total or skin-sparing) or breast-conserving surgery with sentinel lymph node biopsy, and immediate implant or flap-based reconstruction.",
                "total_duration_days": 18,
                "hospital_stay_days": 7,
                "recovery_stay_days": 11,
                "price_usd": "7200.00",
                "includes_flight": True,
                "flight_class": "economy",
                "includes_visa_assistance": True,
                "includes_accommodation": True,
                "accommodation_type": "hotel_4star",
                "includes_transport": True,
                "includes_meals": True,
                "inclusions_text": (
                    "Round-trip economy flights\n"
                    "Airport pickup and drop\n"
                    "7 nights hospital stay\n"
                    "11 nights 4-star hotel\n"
                    "All hospital meals\n"
                    "Pre-op MRI breast + biopsy review\n"
                    "Surgical oncologist + plastic surgeon fees\n"
                    "Implant or tissue expander (if reconstruction)\n"
                    "Sentinel node biopsy + frozen section\n"
                    "Oncology MDT consultation\n"
                    "Visa invitation letter"
                ),
                "exclusions_text": (
                    "Chemotherapy or radiation post-surgery\n"
                    "Travel insurance\n"
                    "Personal expenses"
                ),
                "is_active": True,
            },
            {
                "name": "Gamma Knife Radiosurgery",
                "surgery_type": "Neurosurgery",
                "description": "Non-invasive stereotactic radiosurgery using Leksell Gamma Knife for brain metastases, acoustic neuromas, meningiomas, and arteriovenous malformations.",
                "total_duration_days": 7,
                "hospital_stay_days": 2,
                "recovery_stay_days": 5,
                "price_usd": "9000.00",
                "includes_flight": False,
                "flight_class": "economy",
                "includes_visa_assistance": True,
                "includes_accommodation": True,
                "accommodation_type": "hotel_4star",
                "includes_transport": True,
                "includes_meals": False,
                "inclusions_text": (
                    "2 nights hospital stay\n"
                    "5 nights 4-star hotel\n"
                    "Airport transfers\n"
                    "Pre-treatment MRI + planning CT with frame\n"
                    "Gamma Knife treatment session\n"
                    "Neurosurgeon + radiation oncologist fees\n"
                    "Frame application and removal\n"
                    "Post-treatment neuro-oncology review\n"
                    "Visa support letter"
                ),
                "exclusions_text": (
                    "International flights\n"
                    "Meals\n"
                    "Follow-up MRI scans (after 3 months)\n"
                    "Travel insurance"
                ),
                "is_active": True,
            },
            {
                "name": "Cochlear Implant Surgery",
                "surgery_type": "ENT Surgery",
                "description": "Unilateral cochlear implantation for profound sensorineural hearing loss in adults or children, including pre-op audiological workup and programming sessions.",
                "total_duration_days": 21,
                "hospital_stay_days": 5,
                "recovery_stay_days": 16,
                "price_usd": "11500.00",
                "includes_flight": True,
                "flight_class": "economy",
                "includes_visa_assistance": True,
                "includes_accommodation": True,
                "accommodation_type": "hotel_3star",
                "includes_transport": True,
                "includes_meals": False,
                "inclusions_text": (
                    "Round-trip economy flights\n"
                    "Airport pickup and drop\n"
                    "5 nights hospital stay\n"
                    "16 nights 3-star hotel\n"
                    "Cochlear implant device (Cochlear / MED-EL / AB)\n"
                    "ENT surgeon and anaesthetist fees\n"
                    "Pre-op audiological battery and CT temporal bones\n"
                    "4 post-op programming (mapping) sessions\n"
                    "Auditory rehabilitation guidance\n"
                    "Visa invitation letter"
                ),
                "exclusions_text": (
                    "Hotel meals\n"
                    "Long-term speech therapy (>4 sessions)\n"
                    "Travel insurance\n"
                    "Personal expenses"
                ),
                "is_active": True,
            },
        ],
    },
    # ── Medanta - The Medicity, Gurugram ───────────────────────────────────────
    {
        "name": "Medanta - The Medicity",
        "city": "Gurugram",
        "state": "Haryana",
        "description": (
            "Medanta - The Medicity is a 1,600-bed super-specialty hospital in Gurugram, one of "
            "India's most technologically advanced medical institutions. It excels in spine surgery, "
            "bariatrics, organ transplants, and cardiac sciences. JCI and NABH accredited."
        ),
        "accreditations": "JCI, NABH, NABL",
        "website": "https://www.medanta.org",
        "is_partner": True,
        "packages": [
            {
                "name": "Robotic Spinal Fusion Surgery",
                "surgery_type": "Spine Surgery",
                "description": "Mazor X robotic-guided lumbar or cervical spinal fusion for spondylolisthesis, degenerative disc disease, or spinal stenosis — with sub-millimetre implant accuracy.",
                "total_duration_days": 21,
                "hospital_stay_days": 8,
                "recovery_stay_days": 13,
                "price_usd": "7500.00",
                "includes_flight": True,
                "flight_class": "economy",
                "includes_visa_assistance": True,
                "includes_accommodation": True,
                "accommodation_type": "serviced_apt",
                "includes_transport": True,
                "includes_meals": False,
                "inclusions_text": (
                    "Round-trip economy flights\n"
                    "Airport pickup and drop\n"
                    "8 nights hospital stay\n"
                    "13 nights serviced apartment\n"
                    "Airport transfers throughout stay\n"
                    "Pre-op MRI spine + neuromonitoring setup\n"
                    "Mazor X robotic guidance fee\n"
                    "Titanium interbody cages and pedicle screws\n"
                    "Physiotherapy programme (14 sessions)\n"
                    "Brace/lumbar support\n"
                    "Visa invitation letter"
                ),
                "exclusions_text": (
                    "Meals at serviced apartment\n"
                    "Travel insurance\n"
                    "Personal expenses"
                ),
                "is_active": True,
            },
            {
                "name": "Laparoscopic Sleeve Gastrectomy",
                "surgery_type": "Bariatric Surgery",
                "description": "Laparoscopic sleeve gastrectomy (LSG) removing approximately 80% of the stomach to achieve sustained weight loss in patients with BMI ≥ 35.",
                "total_duration_days": 12,
                "hospital_stay_days": 4,
                "recovery_stay_days": 8,
                "price_usd": "4500.00",
                "includes_flight": True,
                "flight_class": "economy",
                "includes_visa_assistance": True,
                "includes_accommodation": True,
                "accommodation_type": "hotel_3star",
                "includes_transport": True,
                "includes_meals": True,
                "inclusions_text": (
                    "Round-trip economy flights\n"
                    "Airport pickup and drop\n"
                    "4 nights hospital stay\n"
                    "8 nights 3-star hotel\n"
                    "Hospital meals (liquid/pureed post-op diet)\n"
                    "Pre-op metabolic and cardiac clearance\n"
                    "Bariatric surgeon and anaesthetist fees\n"
                    "Bariatric dietitian sessions (3 pre-op + 2 post-op)\n"
                    "Vitamin supplementation kit (1 month)\n"
                    "Visa invitation letter"
                ),
                "exclusions_text": (
                    "Hotel meals\n"
                    "Long-term supplements beyond 1 month\n"
                    "Travel insurance\n"
                    "Personal expenses"
                ),
                "is_active": True,
            },
            {
                "name": "Total Hip Replacement — Medanta",
                "surgery_type": "Orthopedic Surgery",
                "description": "Cementless or hybrid total hip replacement for osteoarthritis or avascular necrosis, with emphasis on early mobilisation and accelerated rehabilitation.",
                "total_duration_days": 14,
                "hospital_stay_days": 5,
                "recovery_stay_days": 9,
                "price_usd": "5500.00",
                "includes_flight": True,
                "flight_class": "economy",
                "includes_visa_assistance": True,
                "includes_accommodation": True,
                "accommodation_type": "hotel_3star",
                "includes_transport": True,
                "includes_meals": False,
                "inclusions_text": (
                    "Round-trip economy flights\n"
                    "Airport transfers\n"
                    "5 nights hospital stay\n"
                    "9 nights 3-star hotel\n"
                    "Cementless hip implant (Zimmer or Stryker)\n"
                    "Pre-op X-ray and blood tests\n"
                    "Physiotherapy (8 sessions)\n"
                    "Walking aids\n"
                    "Visa invitation letter"
                ),
                "exclusions_text": (
                    "Hotel meals\n"
                    "Travel insurance\n"
                    "Personal expenses"
                ),
                "is_active": True,
            },
            {
                "name": "Bariatric Revision Surgery",
                "surgery_type": "Bariatric Surgery",
                "description": "Revisional bariatric surgery for failed primary procedures (sleeve, band, or bypass) with full metabolic re-evaluation and tailored revision strategy.",
                "total_duration_days": 14,
                "hospital_stay_days": 5,
                "recovery_stay_days": 9,
                "price_usd": "6800.00",
                "includes_flight": False,
                "flight_class": "economy",
                "includes_visa_assistance": True,
                "includes_accommodation": True,
                "accommodation_type": "hotel_4star",
                "includes_transport": True,
                "includes_meals": True,
                "inclusions_text": (
                    "5 nights hospital stay\n"
                    "9 nights 4-star hotel\n"
                    "Airport transfers\n"
                    "Comprehensive metabolic re-evaluation\n"
                    "Revisional bariatric surgeon fees\n"
                    "All hospital meals\n"
                    "Dietitian follow-up (3 sessions)\n"
                    "Psychological counselling (2 sessions)\n"
                    "Visa invitation letter"
                ),
                "exclusions_text": (
                    "International flights\n"
                    "Hotel meals\n"
                    "Travel insurance\n"
                    "Personal expenses"
                ),
                "is_active": True,
            },
        ],
    },
    # ── Kokilaben Dhirubhai Ambani Hospital, Mumbai ────────────────────────────
    {
        "name": "Kokilaben Dhirubhai Ambani Hospital",
        "city": "Mumbai",
        "state": "Maharashtra",
        "description": (
            "Kokilaben Dhirubhai Ambani Hospital Mumbai is a 750-bed state-of-the-art facility "
            "with India's first da Vinci Xi robotic surgery programme. It is a leading centre "
            "for oncology, urology, gynaecology, and transplant surgery. JCI and NABH accredited."
        ),
        "accreditations": "JCI, NABH",
        "website": "https://www.kokilabenhospital.com",
        "is_partner": True,
        "packages": [
            {
                "name": "Laparoscopic Hysterectomy Package",
                "surgery_type": "Gynecology Surgery",
                "description": "Total laparoscopic hysterectomy (TLH) for uterine fibroids, adenomyosis, or early endometrial cancer with minimal blood loss and rapid recovery.",
                "total_duration_days": 12,
                "hospital_stay_days": 3,
                "recovery_stay_days": 9,
                "price_usd": "3800.00",
                "includes_flight": True,
                "flight_class": "economy",
                "includes_visa_assistance": True,
                "includes_accommodation": True,
                "accommodation_type": "hotel_3star",
                "includes_transport": True,
                "includes_meals": True,
                "inclusions_text": (
                    "Round-trip economy flights\n"
                    "Airport pickup and drop\n"
                    "3 nights hospital stay\n"
                    "9 nights 3-star hotel\n"
                    "All hospital meals\n"
                    "Pre-op ultrasound and blood panel\n"
                    "Gynaecologist and anaesthetist fees\n"
                    "Pathology of excised specimen\n"
                    "Post-op follow-up consultation\n"
                    "Visa invitation letter"
                ),
                "exclusions_text": (
                    "Hotel meals\n"
                    "Travel insurance\n"
                    "Personal expenses"
                ),
                "is_active": True,
            },
            {
                "name": "Robotic Prostatectomy (Radical)",
                "surgery_type": "Urology Surgery",
                "description": "Da Vinci robotic radical prostatectomy for localised prostate cancer with nerve-sparing technique to preserve urinary and sexual function.",
                "total_duration_days": 14,
                "hospital_stay_days": 4,
                "recovery_stay_days": 10,
                "price_usd": "8500.00",
                "includes_flight": True,
                "flight_class": "economy",
                "includes_visa_assistance": True,
                "includes_accommodation": True,
                "accommodation_type": "hotel_4star",
                "includes_transport": True,
                "includes_meals": True,
                "inclusions_text": (
                    "Round-trip economy flights\n"
                    "Airport pickup and drop\n"
                    "4 nights hospital stay\n"
                    "10 nights 4-star hotel recovery\n"
                    "All hospital meals\n"
                    "Pre-op mpMRI prostate + PSMA PET if needed\n"
                    "Da Vinci robotic procedure fee\n"
                    "Urologist and anaesthetist fees\n"
                    "Pelvic floor physiotherapy (4 sessions)\n"
                    "Catheter management and removal\n"
                    "Visa invitation letter"
                ),
                "exclusions_text": (
                    "Radiation or hormonal therapy post-surgery\n"
                    "Travel insurance\n"
                    "Personal expenses"
                ),
                "is_active": True,
            },
            {
                "name": "Kidney Stone PCNL (Percutaneous Nephrolithotomy)",
                "surgery_type": "Urology Surgery",
                "description": "Minimally invasive removal of large or complex kidney stones (>2 cm) via percutaneous nephrolithotomy with fluoroscopy and nephroscopy guidance.",
                "total_duration_days": 10,
                "hospital_stay_days": 4,
                "recovery_stay_days": 6,
                "price_usd": "2800.00",
                "includes_flight": True,
                "flight_class": "economy",
                "includes_visa_assistance": True,
                "includes_accommodation": True,
                "accommodation_type": "hotel_3star",
                "includes_transport": True,
                "includes_meals": True,
                "inclusions_text": (
                    "Round-trip economy flights\n"
                    "Airport pickup and drop\n"
                    "4 nights hospital stay\n"
                    "6 nights 3-star hotel\n"
                    "All hospital meals\n"
                    "Pre-op CT KUB and blood panel\n"
                    "Urologist and anaesthetist fees\n"
                    "Nephroscopy and lithotripsy equipment\n"
                    "Stone analysis (biochemical)\n"
                    "Visa invitation letter"
                ),
                "exclusions_text": (
                    "Hotel meals\n"
                    "Travel insurance\n"
                    "Personal expenses"
                ),
                "is_active": True,
            },
            {
                "name": "Colorectal Cancer Surgery (Robotic Colectomy)",
                "surgery_type": "Oncology Surgery",
                "description": "Robotic right or left hemicolectomy / anterior resection for colorectal cancer with complete mesocolic excision (CME) and lymph node dissection.",
                "total_duration_days": 18,
                "hospital_stay_days": 7,
                "recovery_stay_days": 11,
                "price_usd": "8200.00",
                "includes_flight": True,
                "flight_class": "economy",
                "includes_visa_assistance": True,
                "includes_accommodation": True,
                "accommodation_type": "hotel_4star",
                "includes_transport": True,
                "includes_meals": True,
                "inclusions_text": (
                    "Round-trip economy flights\n"
                    "Airport pickup and drop\n"
                    "7 nights hospital stay\n"
                    "11 nights 4-star hotel\n"
                    "All hospital meals\n"
                    "Pre-op colonoscopy + PET-CT\n"
                    "Surgical oncologist + anaesthetist fees\n"
                    "Robotic system (da Vinci) fee\n"
                    "Pathology and staging report\n"
                    "Stoma care education if applicable\n"
                    "Visa invitation letter"
                ),
                "exclusions_text": (
                    "Adjuvant chemotherapy post-surgery\n"
                    "Travel insurance\n"
                    "Personal expenses"
                ),
                "is_active": True,
            },
        ],
    },
    # ── Yashoda Hospitals, Hyderabad ───────────────────────────────────────────
    {
        "name": "Yashoda Hospitals",
        "city": "Hyderabad",
        "state": "Telangana",
        "description": (
            "Yashoda Hospitals Hyderabad is a 1,000-bed multi-speciality hospital chain renowned "
            "for ophthalmology, ENT, urology, pulmonology, and dental care across South India. "
            "NABH accredited with a strong international patient programme."
        ),
        "accreditations": "NABH, NABL",
        "website": "https://www.yashodahospitals.com",
        "is_partner": True,
        "packages": [
            {
                "name": "Advanced LASIK & Cataract Surgery Package",
                "surgery_type": "Eye Surgery",
                "description": "Bladeless femtosecond LASIK for refractive errors, or phacoemulsification cataract removal with premium IOL implantation (multifocal or toric).",
                "total_duration_days": 8,
                "hospital_stay_days": 1,
                "recovery_stay_days": 7,
                "price_usd": "1800.00",
                "includes_flight": True,
                "flight_class": "economy",
                "includes_visa_assistance": True,
                "includes_accommodation": True,
                "accommodation_type": "hotel_3star",
                "includes_transport": True,
                "includes_meals": False,
                "inclusions_text": (
                    "Round-trip economy flights\n"
                    "Airport pickup and drop\n"
                    "1 night hospital/clinic stay\n"
                    "7 nights 3-star hotel\n"
                    "Pre-op corneal topography, pachymetry, biometry\n"
                    "Ophthalmologist consultation + surgery fees\n"
                    "IOL implant (if cataract) or laser ablation fee\n"
                    "Post-op eye drops kit (1 month supply)\n"
                    "2 follow-up consultations during stay\n"
                    "Visa invitation letter"
                ),
                "exclusions_text": (
                    "Hotel meals\n"
                    "Travel insurance\n"
                    "Personal expenses"
                ),
                "is_active": True,
            },
            {
                "name": "Cochlear Implant Surgery — Yashoda",
                "surgery_type": "ENT Surgery",
                "description": "Cochlear implant for severe-to-profound sensorineural hearing loss. Package includes audiological evaluation, surgery, and four mapping (programming) sessions.",
                "total_duration_days": 21,
                "hospital_stay_days": 4,
                "recovery_stay_days": 17,
                "price_usd": "8000.00",
                "includes_flight": True,
                "flight_class": "economy",
                "includes_visa_assistance": True,
                "includes_accommodation": True,
                "accommodation_type": "hotel_3star",
                "includes_transport": True,
                "includes_meals": False,
                "inclusions_text": (
                    "Round-trip economy flights\n"
                    "Airport pickup and drop\n"
                    "4 nights hospital stay\n"
                    "17 nights 3-star hotel\n"
                    "Cochlear implant device (leading brand)\n"
                    "ENT surgeon and anaesthetist fees\n"
                    "Pre-op audiometry, BERA, CT temporal bone\n"
                    "4 processor mapping sessions during stay\n"
                    "Rehabilitation guidance booklet\n"
                    "Visa invitation letter"
                ),
                "exclusions_text": (
                    "Hotel meals\n"
                    "Travel insurance\n"
                    "Personal expenses"
                ),
                "is_active": True,
            },
            {
                "name": "Robotic Prostatectomy — Yashoda",
                "surgery_type": "Urology Surgery",
                "description": "Robotic-assisted laparoscopic radical prostatectomy for organ-confined prostate cancer with nerve-sparing approach and early catheter removal protocol.",
                "total_duration_days": 14,
                "hospital_stay_days": 4,
                "recovery_stay_days": 10,
                "price_usd": "7200.00",
                "includes_flight": True,
                "flight_class": "economy",
                "includes_visa_assistance": True,
                "includes_accommodation": True,
                "accommodation_type": "hotel_4star",
                "includes_transport": True,
                "includes_meals": True,
                "inclusions_text": (
                    "Round-trip economy flights\n"
                    "Airport pickup and drop\n"
                    "4 nights hospital stay\n"
                    "10 nights 4-star hotel recovery\n"
                    "All hospital meals\n"
                    "Pre-op mpMRI prostate\n"
                    "Robotic surgery fee\n"
                    "Urologist and anaesthetist fees\n"
                    "Pelvic floor physiotherapy (3 sessions)\n"
                    "Visa invitation letter"
                ),
                "exclusions_text": (
                    "Radiation or hormonal therapy post-surgery\n"
                    "Travel insurance\n"
                    "Personal expenses"
                ),
                "is_active": True,
            },
            {
                "name": "VATS Lung Surgery (Thoracoscopy)",
                "surgery_type": "Pulmonology Surgery",
                "description": "Video-assisted thoracoscopic surgery (VATS) for lung nodule excision, pleural effusion management, or wedge resection for early-stage lung cancer.",
                "total_duration_days": 16,
                "hospital_stay_days": 6,
                "recovery_stay_days": 10,
                "price_usd": "6500.00",
                "includes_flight": True,
                "flight_class": "economy",
                "includes_visa_assistance": True,
                "includes_accommodation": True,
                "accommodation_type": "hotel_4star",
                "includes_transport": True,
                "includes_meals": True,
                "inclusions_text": (
                    "Round-trip economy flights\n"
                    "Airport pickup and drop\n"
                    "6 nights hospital stay\n"
                    "10 nights 4-star hotel\n"
                    "All hospital meals\n"
                    "Pre-op PET-CT or high-res CT chest\n"
                    "Thoracic surgeon + anaesthetist fees\n"
                    "VATS equipment and disposables\n"
                    "ICU monitoring (1 night post-op)\n"
                    "Respiratory physiotherapy (6 sessions)\n"
                    "Pathology of excised specimen\n"
                    "Visa invitation letter"
                ),
                "exclusions_text": (
                    "Adjuvant chemotherapy if malignant\n"
                    "Travel insurance\n"
                    "Personal expenses"
                ),
                "is_active": True,
            },
            {
                "name": "Full Mouth Dental Rehabilitation",
                "surgery_type": "Dental Surgery",
                "description": "Comprehensive full-mouth reconstruction including implants, crowns, bone grafting, and aesthetic veneers — all under one coordinated treatment plan.",
                "total_duration_days": 14,
                "hospital_stay_days": 0,
                "recovery_stay_days": 14,
                "price_usd": "4000.00",
                "includes_flight": True,
                "flight_class": "economy",
                "includes_visa_assistance": True,
                "includes_accommodation": True,
                "accommodation_type": "hotel_3star",
                "includes_transport": True,
                "includes_meals": False,
                "inclusions_text": (
                    "Round-trip economy flights\n"
                    "Airport pickup and drop\n"
                    "14 nights 3-star hotel\n"
                    "Daily transport to dental clinic\n"
                    "Initial OPG X-ray + CBCT scan\n"
                    "Comprehensive dental examination\n"
                    "Up to 6 dental implants (titanium)\n"
                    "Ceramic crowns (up to 8)\n"
                    "Bone grafting if required\n"
                    "Temporary and final prosthetics\n"
                    "Post-procedure care kit\n"
                    "Visa invitation letter"
                ),
                "exclusions_text": (
                    "Hotel meals\n"
                    "Travel insurance\n"
                    "Additional implants beyond package\n"
                    "Personal expenses"
                ),
                "is_active": True,
            },
            {
                "name": "Laparoscopic Cholecystectomy & GI Package",
                "surgery_type": "Gastroenterology Surgery",
                "description": "Laparoscopic removal of the gallbladder for symptomatic gallstones or cholecystitis, combined with upper GI endoscopy for complete abdominal evaluation.",
                "total_duration_days": 8,
                "hospital_stay_days": 2,
                "recovery_stay_days": 6,
                "price_usd": "2200.00",
                "includes_flight": True,
                "flight_class": "economy",
                "includes_visa_assistance": True,
                "includes_accommodation": True,
                "accommodation_type": "hotel_3star",
                "includes_transport": True,
                "includes_meals": True,
                "inclusions_text": (
                    "Round-trip economy flights\n"
                    "Airport pickup and drop\n"
                    "2 nights hospital stay\n"
                    "6 nights 3-star hotel\n"
                    "All hospital meals\n"
                    "Pre-op ultrasound abdomen + LFT panel\n"
                    "Laparoscopic surgeon and anaesthetist fees\n"
                    "Upper GI endoscopy\n"
                    "Post-op dietary advice\n"
                    "Visa invitation letter"
                ),
                "exclusions_text": (
                    "Hotel meals\n"
                    "Travel insurance\n"
                    "Personal expenses"
                ),
                "is_active": True,
            },
        ],
    },
]


class Command(BaseCommand):
    help = "Seed the database with dummy development data."

    def add_arguments(self, parser):
        parser.add_argument(
            "--flush",
            action="store_true",
            help="Delete all existing seed data before re-creating.",
        )
        parser.add_argument(
            "--with-demo-workflow",
            action="store_true",
            help="Also seed a complete sample workflow (intake → match → consultation → "
                 "prescription → surgery recommendation → admin approval → booking → chat). "
                 "Useful for demos so dashboards aren't empty.",
        )

    def handle(self, *args, **options):
        if options["flush"]:
            self._flush()

        self._fix_null_users()
        self._seed_specializations()
        self._seed_admin()
        self._seed_patients()
        self._seed_doctors()
        self._seed_hospitals()

        if options["with_demo_workflow"]:
            self._seed_demo_workflow()

        self.stdout.write(self.style.SUCCESS("\nSeed complete.\n"))
        self._print_credentials()

    # ------------------------------------------------------------------

    def _fix_null_users(self):
        """Fix any users left with NULL role or NULL is_email_verified (e.g. from early signups)."""
        fixed = User.objects.filter(role__isnull=True).update(role="patient")
        fixed += User.objects.filter(role="").update(role="patient")
        fixed2 = User.objects.filter(is_email_verified__isnull=True).update(is_email_verified=False)
        if fixed or fixed2:
            self.stdout.write(f"  Fixed {fixed} NULL-role users, {fixed2} NULL-verified users.")

    def _flush(self):
        self.stdout.write("Flushing existing seed data...")
        emails = (
            ["admin@test.local", "patient@test.local", "patient2@test.local"]
            + [d["email"] for d in DOCTORS]
        )
        # User deletion CASCADEs through profiles, appointments, intakes, recs, messages, etc.
        User.objects.filter(email__in=emails).delete()

        # SurgeryPackage.hospital uses PROTECT — clear ALL bookings + recommendations
        # first (including any from non-seed real-signup users) so hospitals can be deleted.
        # This is what "flush" implies — wipe workflow tables for a clean re-seed.
        SurgeryPackageBooking.objects.all().delete()
        SurgeryRecommendation.objects.all().delete()
        Hospital.objects.filter(name__in=[h["name"] for h in HOSPITALS]).delete()
        self.stdout.write("  Flushed.\n")

    # ------------------------------------------------------------------

    def _seed_specializations(self):
        self.stdout.write("Seeding specializations...")
        for s in SPECIALIZATIONS:
            obj, created = Specialization.objects.get_or_create(
                slug=s["slug"], defaults={"name": s["name"]}
            )
            if created:
                self.stdout.write(f"  + {obj.name}")

    def _seed_admin(self):
        self.stdout.write("Seeding admin user...")
        user, created = User.objects.get_or_create(
            email="admin@test.local",
            defaults={"role": "admin", "is_staff": True, "is_superuser": True, "is_email_verified": True},
        )
        user.set_password(PASSWORD)
        user.is_email_verified = True
        user.save(update_fields=["password", "is_email_verified"])
        self.stdout.write(f"  {'+ ' if created else '  (reset password) '}admin@test.local")

    def _seed_patients(self):
        self.stdout.write("Seeding patient users...")

        patients = [
            {
                "email": "patient@test.local",
                "first_name": "Sarah",
                "last_name": "Johnson",
                "date_of_birth": datetime.date(1990, 6, 15),
                "gender": "female",
                "blood_group": "O+",
                "phone": "+1-416-555-0101",
                "country": "Canada",
                "state": "Ontario",
                "city": "Toronto",
                "address_line": "42 Maple Street",
                "postal_code": "M5V 2T6",
                "timezone": "America/Toronto",
                "height_cm": 165,
                "weight_kg": "62.50",
                "existing_conditions": "Mild hypertension",
                "allergies": "Penicillin",
                "current_medications": "Amlodipine 5mg daily",
                "emergency_contact_name": "Michael Johnson",
                "emergency_contact_phone": "+1-416-555-0199",
            },
            {
                "email": "patient2@test.local",
                "first_name": "John",
                "last_name": "Doe",
                "date_of_birth": datetime.date(1985, 3, 22),
                "gender": "male",
                "blood_group": "A+",
                "phone": "+1-212-555-0202",
                "country": "USA",
                "state": "New York",
                "city": "New York City",
                "address_line": "101 Park Avenue",
                "postal_code": "10178",
                "timezone": "America/New_York",
                "height_cm": 180,
                "weight_kg": "85.00",
                "existing_conditions": "Type 2 Diabetes, Knee osteoarthritis",
                "allergies": "",
                "current_medications": "Metformin 500mg twice daily",
                "emergency_contact_name": "Jane Doe",
                "emergency_contact_phone": "+1-212-555-0299",
            },
        ]

        for p in patients:
            email = p.pop("email")
            user, created = User.objects.get_or_create(
                email=email,
                defaults={"role": "patient", "is_email_verified": True},
            )
            user.set_password(PASSWORD)
            user.is_email_verified = True
            user.save(update_fields=["password", "is_email_verified"])

            PatientProfile.objects.filter(user=user).update(**p)
            self.stdout.write(f"  {'+ ' if created else '  (reset) '}{email}")

    def _seed_doctors(self):
        self.stdout.write("Seeding doctor users...")

        for d in DOCTORS:
            email = d["email"]
            existing = User.objects.filter(email=email).first()
            if existing:
                existing.set_password(PASSWORD)
                existing.is_email_verified = True
                existing.save(update_fields=["password", "is_email_verified"])
                self.stdout.write(f"  (reset) {email}")
                continue

            user = User.objects.create_user(
                email=email, password=PASSWORD, role="doctor", is_email_verified=True
            )

            spec_names = d.pop("specializations")
            education_data = d.pop("education")
            slots_data = d.pop("slots")

            profile = DoctorProfile.objects.create(
                user=user,
                is_verified=True,
                is_available=True,
                **{k: v for k, v in d.items() if k != "email"},
            )

            specs = Specialization.objects.filter(name__in=spec_names)
            profile.specializations.set(specs)

            for edu in education_data:
                DoctorEducation.objects.create(doctor=profile, **edu)

            for slot in slots_data:
                DoctorAvailabilitySlot.objects.create(
                    doctor=profile,
                    slot_type="recurring_weekly",
                    day_of_week=slot["day"],
                    start_time=slot["start"],
                    end_time=slot["end"],
                    is_active=True,
                )

            self.stdout.write(f"  + {email} ({profile.first_name} {profile.last_name})")

    def _seed_hospitals(self):
        self.stdout.write("Seeding hospitals and surgery packages...")

        for h in HOSPITALS:
            packages_data = h.pop("packages", [])
            hospital, created = Hospital.objects.get_or_create(
                name=h["name"],
                defaults=h,
            )
            if created:
                self.stdout.write(f"  + Hospital: {hospital.name}, {hospital.city}")
            else:
                self.stdout.write(f"  Hospital: {hospital.name} (exists)")

            for pkg in packages_data:
                _, pkg_created = SurgeryPackage.objects.get_or_create(
                    hospital=hospital,
                    name=pkg["name"],
                    defaults=pkg,
                )
                if pkg_created:
                    self.stdout.write(f"    + Package: {pkg['name']}")

    # ------------------------------------------------------------------

    def _seed_demo_workflow(self):
        """Seed a realistic, end-to-end sample workflow so the demo dashboards aren't empty.

        Creates:
          • 1 PENDING intake from Sarah (severe knee pain) — admin can match it live
          • 1 MATCHED intake from John (gynecology) → COMPLETED appointment → prescription written
            → surgery recommended → admin APPROVED → patient BOOKED + paid → 2 chat messages
          • 1 PENDING surgery recommendation (different patient + doctor) so admin sees something to approve
        """
        self.stdout.write("Seeding demo workflow data...")

        admin    = User.objects.filter(role="admin").first()
        sarah    = PatientProfile.objects.filter(user__email="patient@test.local").first()
        john     = PatientProfile.objects.filter(user__email="patient2@test.local").first()
        mishra   = DoctorProfile.objects.filter(user__email="dr.mishra@test.local").first()   # Gynecology
        patel    = DoctorProfile.objects.filter(user__email="dr.patel@test.local").first()    # Orthopedics

        if not all([admin, sarah, john, mishra, patel]):
            self.stdout.write(self.style.WARNING(
                "  Skipping workflow seed — missing one of admin/patients/doctors."
            ))
            return

        # ── 1. Sarah's pending intake (admin will see this in /admin/intakes) ────
        SymptomIntake.objects.get_or_create(
            patient=sarah,
            chief_complaint="Severe knee pain and difficulty walking",
            defaults={
                "symptoms": (
                    "Sharp pain in right knee for 3 weeks. Worsens with stairs and "
                    "prolonged standing. Audible clicking when bending. Visible swelling."
                ),
                "duration": "3 weeks",
                "severity": "severe",
                "existing_conditions_note": "Hypertension, on Amlodipine 5mg.",
                "preferred_doctor": patel,
                "status": "pending",
            },
        )
        self.stdout.write(f"  + Pending intake from {sarah.user.email} (knee pain)")

        # ── 2. John's full completed workflow (gynecology, but using a gender-neutral case) ──
        intake_john, _ = SymptomIntake.objects.get_or_create(
            patient=john,
            chief_complaint="Recurring abdominal pain after meals",
            defaults={
                "symptoms": (
                    "Pain in upper-right abdomen after eating, especially fatty meals. "
                    "Started 6 weeks ago. Occasional nausea. Pain rates 6/10."
                ),
                "duration": "6 weeks",
                "severity": "moderate",
                "existing_conditions_note": "Type 2 Diabetes, on Metformin 500mg.",
                "preferred_doctor": mishra,
                "status": "matched",
                "matched_doctor": mishra,
                "matched_by": admin,
                "matched_at": timezone.now() - datetime.timedelta(days=4),
                "admin_notes": "Routed to Dr. Mishra for evaluation. Likely gallbladder-related.",
            },
        )
        self.stdout.write(f"  + Matched intake from {john.user.email} (abdominal pain)")

        # Completed appointment (3 days ago)
        appt_start = timezone.now() - datetime.timedelta(days=3, hours=2)
        appt, _ = Appointment.objects.get_or_create(
            patient=john, doctor=mishra,
            scheduled_start=appt_start,
            defaults={
                "intake": intake_john,
                "scheduled_end": appt_start + datetime.timedelta(minutes=30),
                "status": "completed",
                "payment_ref": f"DUMMY-{secrets.token_hex(6).upper()}",
                "meeting_link": f"https://meet.jit.si/medibridge-{secrets.token_hex(8)}",
                "completed_at": appt_start + datetime.timedelta(minutes=28),
                "notes": "Patient reports gallbladder-pattern pain. Recommended laparoscopic evaluation.",
            },
        )
        self.stdout.write(f"  + Completed appointment #{appt.id}")

        # Prescription with medicines + tests
        rx, rx_created = Prescription.objects.get_or_create(
            appointment=appt,
            defaults={
                "diagnosis": "Suspected symptomatic cholelithiasis (gallstones).",
                "general_notes": "Avoid fatty meals. Stay hydrated. Return if pain worsens or fever develops.",
                "follow_up_required": True,
                "follow_up_after_days": 14,
            },
        )
        if rx_created:
            PrescriptionMedicine.objects.bulk_create([
                PrescriptionMedicine(
                    prescription=rx, medicine_name="Pantoprazole",
                    dosage="40mg", morning=True, evening=False, night=False, afternoon=False,
                    meal_timing="before_meal", duration_days=14,
                    instructions="Take 30 min before breakfast.",
                ),
                PrescriptionMedicine(
                    prescription=rx, medicine_name="Drotaverine",
                    dosage="80mg", morning=True, afternoon=False, evening=True, night=False,
                    meal_timing="after_meal", duration_days=7,
                    instructions="Take only when pain occurs.",
                ),
            ])
            PrescribedTest.objects.bulk_create([
                PrescribedTest(
                    prescription=rx, test_name="Abdominal Ultrasound", urgency="urgent",
                    instructions="Confirm presence and size of gallstones.",
                ),
                PrescribedTest(
                    prescription=rx, test_name="Liver Function Tests (LFT)", urgency="routine",
                    instructions="Rule out bile duct involvement.",
                ),
            ])
        self.stdout.write(f"  + Prescription with 2 medicines + 2 tests")

        # Surgery recommendation — pick a gastroenterology package
        from apps.hospitals.models import SurgeryPackage as Pkg
        chole_pkg = Pkg.objects.filter(surgery_type__icontains="Gastro").first() \
                 or Pkg.objects.filter(name__icontains="Cholecyst").first() \
                 or Pkg.objects.first()
        rec, rec_created = SurgeryRecommendation.objects.get_or_create(
            doctor=mishra, patient=john, package=chole_pkg,
            defaults={
                "appointment": appt,
                "status": "approved",
                "notes": (
                    "Ultrasound confirmed multiple cholesterol gallstones with thickened "
                    "gallbladder wall. Symptomatic. Recommending laparoscopic cholecystectomy."
                ),
                "admin_notes": "Reviewed and approved. Patient may proceed with booking.",
            },
        )
        self.stdout.write(f"  + Surgery recommendation: {chole_pkg.name} (APPROVED)")

        # Confirmed booking for John
        booking, _ = SurgeryPackageBooking.objects.get_or_create(
            patient=john, package=chole_pkg,
            defaults={
                "status": "confirmed",
                "tentative_date": (timezone.now() + datetime.timedelta(days=30)).date(),
                "total_amount_usd": chole_pkg.price_usd,
                "payment_ref": f"DUMMY-{secrets.token_hex(6).upper()}",
            },
        )
        self.stdout.write(f"  + Surgery booking #{booking.id} CONFIRMED")

        # Sample chat messages — admin↔doctor + admin↔patient (so unread badges show in demo)
        if rec_created or not RecommendationMessage.objects.filter(recommendation=rec).exists():
            RecommendationMessage.objects.create(
                recommendation=rec, thread_type="doctor", sender=admin,
                sender_role="admin",
                body="Hi Dr. Mishra — could you confirm the ultrasound report shows multiple stones, not sludge?",
                read_by_admin=True, read_by_doctor=False,
            )
            RecommendationMessage.objects.create(
                recommendation=rec, thread_type="doctor", sender=mishra.user,
                sender_role="doctor",
                body="Yes, ultrasound clearly shows 3 stones, largest 1.2cm. Cholesterol composition. Surgery is indicated.",
                read_by_admin=False, read_by_doctor=True,
            )
            RecommendationMessage.objects.create(
                recommendation=rec, thread_type="patient", sender=john.user,
                sender_role="patient",
                body="What does the recovery time look like after this surgery?",
                read_by_admin=False, read_by_patient=True,
            )
            self.stdout.write(f"  + 3 sample chat messages on rec #{rec.id}")

        # ── 3. One more pending recommendation for the orthopedic doctor (different patient) ──
        # so admin's "Pending Surgery Recs" KPI > 0 even after approving the first one
        ortho_pkg = Pkg.objects.filter(surgery_type__icontains="Orthopedic").first() \
                 or Pkg.objects.filter(name__icontains="Knee").first()
        if ortho_pkg:
            SurgeryRecommendation.objects.get_or_create(
                doctor=patel, patient=sarah, package=ortho_pkg,
                defaults={
                    "status": "pending_admin",
                    "notes": (
                        "MRI confirms Grade III chondromalacia. Conservative therapy has failed. "
                        "Recommending arthroscopic intervention."
                    ),
                },
            )
            self.stdout.write(f"  + Pending surgery recommendation: {ortho_pkg.name}")

    # ------------------------------------------------------------------

    def _print_credentials(self):
        self.stdout.write(self.style.SUCCESS("-" * 70))
        self.stdout.write(self.style.SUCCESS("  DEMO LOGIN CREDENTIALS  (password: Test@1234)"))
        self.stdout.write(self.style.SUCCESS("-" * 70))
        rows = [
            ("admin@test.local",           "Admin"),
            ("patient@test.local",         "Patient — Sarah Johnson (Canada)"),
            ("patient2@test.local",        "Patient — John Doe (USA)"),
            ("", ""),
            ("dr.sharma@test.local",       "Cardiology — Dr. Rajesh Sharma (18 yrs, Apollo Delhi)"),
            ("dr.kapoor@test.local",       "Cardiology — Dr. Arjun Kapoor (3 yrs, Narayana Bangalore)"),
            ("dr.patel@test.local",        "Orthopedics — Dr. Priya Patel (13 yrs, Fortis Mumbai)"),
            ("dr.nair@test.local",         "Orthopedics — Dr. Deepa Nair (5 yrs, Narayana Bangalore)"),
            ("dr.mehta@test.local",        "Neurology — Dr. Amit Mehta (11 yrs, Manipal Bangalore)"),
            ("dr.krishna@test.local",      "Neurology — Dr. Venkata Krishna (22 yrs, Max Delhi)"),
            ("dr.roy@test.local",          "Oncology — Dr. Sunita Roy (15 yrs, Tata Memorial Mumbai)"),
            ("dr.gupta@test.local",        "Oncology — Dr. Ravi Gupta (7 yrs, Kokilaben Mumbai)"),
            ("dr.malhotra@test.local",     "General Surgery — Dr. Anil Malhotra (9 yrs, Medanta Gurugram)"),
            ("dr.pillai@test.local",       "General Surgery — Dr. Lakshmi Pillai (2 yrs, Apollo Delhi)"),
            ("dr.joshi@test.local",        "Gastroenterology — Dr. Suresh Joshi (14 yrs, Medanta Gurugram)"),
            ("dr.bose@test.local",         "Gastroenterology — Dr. Ananya Bose (4 yrs, Yashoda Hyderabad)"),
            ("dr.mishra@test.local",       "Gynecology — Dr. Kavita Mishra (17 yrs, Kokilaben Mumbai)"),
            ("dr.agarwal@test.local",      "Gynecology — Dr. Pooja Agarwal (5 yrs, Manipal Bangalore)"),
            ("dr.verma@test.local",        "Ophthalmology — Dr. Sanjay Verma (10 yrs, Yashoda Hyderabad)"),
            ("dr.sinha@test.local",        "Ophthalmology — Dr. Preethi Sinha (3 yrs, Fortis Mumbai)"),
            ("dr.reddy@test.local",        "Pulmonology — Dr. Suresh Reddy (15 yrs, Yashoda Hyderabad)"),
            ("dr.iyer@test.local",         "Pulmonology — Dr. Meera Iyer (6 yrs, Manipal Bangalore)"),
            ("dr.pandey@test.local",       "Urology — Dr. Vivek Pandey (12 yrs, Kokilaben Mumbai)"),
            ("dr.chandra@test.local",      "Urology — Dr. Geeta Chandra (4 yrs, Yashoda Hyderabad)"),
            ("dr.saxena@test.local",       "ENT Surgery — Dr. Rohit Saxena (11 yrs, Max Delhi)"),
            ("dr.desai@test.local",        "ENT Surgery — Dr. Nandita Desai (4 yrs, Yashoda Hyderabad)"),
            ("dr.chatterjee@test.local",   "Neurosurgery — Dr. Biplab Chatterjee (13 yrs, Max Delhi)"),
            ("dr.tiwari@test.local",       "Neurosurgery — Dr. Shalini Tiwari (5 yrs, Manipal Bangalore)"),
        ]
        for email, label in rows:
            if not email:
                self.stdout.write("")
            else:
                self.stdout.write(f"  {email:<35}  {label}")
        self.stdout.write(self.style.SUCCESS("-" * 70))
