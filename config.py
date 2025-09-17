import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY','5e65fc76fa088a47052d9290858b24cf7815699e5553e66e18f18c07e17bcdef')
    SUPABASE_URL = os.environ.get('SUPABASE_URL','https://bcumkrzvgbjepxpghahz.supabase.co')
    SUPABASE_KEY = os.environ.get('SUPABASE_KEY','eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJjdW1rcnp2Z2JqZXB4cGdoYWh6Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTgwODMxNzMsImV4cCI6MjA3MzY1OTE3M30.BUZSXAXtcjxW3ZPoB_s1Mch_L40d4XCb2mOQEv0m6dw')
ADMIN_EMAILS = os.environ.get('ADMIN_EMAILS', 'admin@example.com').split(',')
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'admin123')

    