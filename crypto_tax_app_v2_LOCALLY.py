
import os
import pandas as pd
from flask import Flask, request, render_template_string, redirect, url_for, flash, session
from flask_session import Session # *** Import Flask-Session ***
from werkzeug.utils import secure_filename
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation
import io
import traceback
import datetime
from collections import defaultdict
import time # Temporary for simulating processing time

# --- Configuration ---
UPLOAD_FOLDER = 'uploads_temp' # Temporary storage for uploads
ALLOWED_EXTENSIONS = {'csv'}
DECIMAL_PLACES = 8 # Precision for crypto amounts
CURRENCY_PLACES = 2 # Precision for CAD values

# Column Name Mappings (French to English) - Keep as is
FRENCH_TO_ENGLISH_MAP = {
    "Date": "Date", "Montant débité": "Amount Debited", "Actif débité": "Asset Debited",
    "Montant crédité": "Amount Credited", "Actif crédité": "Asset Credited", "Valeur du marché": "Market Value",
    "Devise de valeur du marché": "Market Value Currency", "Coût comptable": "Book Cost",
    "Devise du coût comptable": "Book Cost Currency", "Type": "Type", "Taux au comptant": "Spot Rate",
    "Taux d'achat/de vente": "Buy / Sell Rate", "Description": "Description"
}

# Transaction Type Mappings (French to English) - Keep as is
FRENCH_TO_ENGLISH_TYPES = {
    "Achat": "Buy", "Récompenses": "Reward", "Envoi": "Send", "Vente": "Sell",
    "Recevoir": "Receive", "Remise en bitcoins": "Reward", "Remises en Bitcoin": "Reward"
}

# --- Embedded CSS (Updated with New Design) ---
EMBEDDED_CSS = """
<style>
    /* Updated Quebec Crypto Tax Helper CSS */

    :root {
      --primary: #0047A0;        /* Quebec blue */
      --primary-dark: #003780;   /* Darker Quebec blue for hover */
      --primary-light: #3399FF;  /* Lighter blue for accents */
      --secondary: #22c55e;      /* Green for success/actions */
      --secondary-dark: #16a34a; /* Darker green for hover */
      --gray-100: #f3f4f6;       /* Lightest gray for backgrounds */
      --gray-200: #e5e7eb;       /* Light gray for borders/dividers */
      --gray-300: #d1d5db;       /* Medium gray for borders */
      --gray-600: #4b5563;       /* Dark gray for text/labels */
      --gray-800: #1f2937;       /* Darkest gray for headings */
      --success: #16a34a;        /* Darker green for text */
      --success-bg: #dcfce7;     /* Light green background */
      --danger: #dc2626;         /* Red for errors */
      --danger-bg: #fee2e2;      /* Light red background */
      --info: #2563eb;           /* Blue for info */
      --info-bg: #dbeafe;        /* Light blue background */
      --warning: #f59e0b;        /* Amber for warnings */
      --warning-bg: #fef3c7;     /* Light amber background */
      --card-shadow: 0 4px 12px -2px rgba(0, 71, 160, 0.15), 0 2px 6px -1px rgba(0, 71, 160, 0.1);
      --font-sans: 'Nunito', system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
      --gradient-main: linear-gradient(135deg, #2196F3 0%, #6C5CE7 100%); /* Adjusted slightly for a more vibrant feel */
      --gradient-button: linear-gradient(135deg, #0047A0 0%, #3399FF 100%);
    }

    /* --- Google Font Import --- */
    @import url('https://fonts.googleapis.com/css2?family=Nunito:wght@400;500;600;700&display=swap');

    /* --- General Body & Container --- */
    body {
      font-family: var(--font-sans);
      /* background: var(--gradient-main); */ /* Commented out gradient on body for better readability, applied elsewhere if needed */
      background-color: var(--gray-100); /* Use light gray as base background */
      background-attachment: fixed;
      line-height: 1.6;
      color: var(--gray-800);
      padding: 0;
      margin: 0;
      display: flex;
      flex-direction: column;
      min-height: 100vh;
    }

    .main-content {
      flex-grow: 1;
    }

    .container {
      max-width: 900px;
      margin: 40px auto;
      background-color: white;
      border-radius: 16px; /* Increased border radius */
      box-shadow: var(--card-shadow);
      padding: 32px;
      position: relative;
      overflow: hidden; /* Important for pseudo-element */
    }

    /* Add subtle Quebec flag pattern to container */
    /* Disabled by default as it can be distracting, uncomment if desired */
    /*
    .container::before {
      content: '';
      position: absolute;
      top: 0;
      right: 0;
      width: 80px;
      height: 80px;
      background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'%3E%3Crect width='100' height='100' fill='%230047A0' /%3E%3Cpath d='M50 15 L85 50 L50 85 L15 50 Z' fill='white' /%3E%3Cpath d='M30 30 Q35 40 30 50 Q25 40 30 30 Z M70 30 Q75 40 70 50 Q65 40 70 30 Z M30 50 Q35 60 30 70 Q25 60 30 50 Z M70 50 Q75 60 70 70 Q65 60 70 50 Z' fill='%230047A0' /%3E%3C/svg%3E");
      background-size: contain;
      opacity: 0.05;
      pointer-events: none;
      z-index: 0;
    }
    */
    /* --- Header --- */
    .app-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding-bottom: 20px;
      margin-bottom: 30px;
      border-bottom: 1px solid var(--gray-200);
      position: relative; /* Ensure header content is above pseudo-elements if they exist */
      z-index: 1;
    }

    .logo {
      display: flex;
      align-items: center;
      gap: 12px;
      text-decoration: none;
      position: relative;
    }

    .logo-icon {
      font-size: 1.8rem; /* Original Bitcoin icon size */
      color: var(--primary);
      /* Raccoon/Mask Icon - Uncomment below if you prefer the SVG icon */
      /*
      display: inline-block;
      background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 36 36' fill='%230047A0'%3E%3Cpath d='M18,12c-8,0-12,4-12,4s4,8,12,8s12-8,12-8S26,12,18,12z'/%3E%3Ccircle cx='18' cy='16' r='5' fill='white'/%3E%3Ccircle cx='18' cy='16' r='3' fill='%230047A0'/%3E%3Cpath d='M7,8c0,0,2,4,5,6C7,14,7,8,7,8z'/%3E%3Cpath d='M29,8c0,0-2,4-5,6C29,14,29,8,29,8z'/%3E%3C/svg%3E");
      width: 36px;
      height: 36px;
      vertical-align: middle;
      */
    }

    .logo-text {
      font-size: 1.3rem; /* Increased size */
      font-weight: 700;
      color: var(--gray-800);
      text-shadow: 0px 1px 1px rgba(0, 0, 0, 0.1);
    }

    .main-nav {
      display: flex;
      gap: 16px;
    }

    .nav-link {
      color: var(--gray-600);
      text-decoration: none;
      font-weight: 600; /* Bolder nav links */
      padding: 10px 14px; /* Slightly larger padding */
      border-radius: 8px;
      transition: all 0.2s ease;
    }

    .nav-link:hover, .nav-link.active {
      background-color: rgba(0, 71, 160, 0.1); /* Subtle hover background */
      color: var(--primary);
    }

    /* --- Footer --- */
    .app-footer {
      margin-top: auto;
      padding: 20px 0;
      /* background-color: rgba(255, 255, 255, 0.9); */ /* Using solid white for footer */
      background-color: white;
      border-top: 1px solid rgba(0, 71, 160, 0.1); /* Subtle border */
    }

    .footer-content {
      max-width: 900px;
      margin: 0 auto;
      padding: 0 32px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      font-size: 0.875rem;
      color: var(--gray-600);
      flex-wrap: wrap;
      gap: 10px;
    }

    .footer-links {
      display: flex;
      gap: 16px;
    }

    .footer-links a {
      color: var(--primary); /* Links match primary color */
      text-decoration: none;
      font-weight: 500;
    }

    .footer-links a:hover {
      color: var(--primary-dark);
      text-decoration: underline;
    }


    /* --- Headings --- */
    h1 {
      color: var(--primary);
      font-size: 1.8rem;
      font-weight: 700;
      margin: 0 0 20px 0;
      padding-bottom: 15px;
      border-bottom: 3px solid var(--primary);
      text-align: center;
      position: relative;
    }
    /* Bitcoin symbol below h1 heading */
    h1::after {
      content: '₿';
      position: absolute;
      bottom: -12px; /* Position below the border */
      left: 50%;
      transform: translateX(-50%);
      background: white; /* Match container background */
      padding: 0 12px;
      font-size: 1.5rem;
      color: var(--primary);
    }


    h2 {
      color: var(--primary-dark); /* Darker blue for H2 */
      font-size: 1.4rem;
      margin-top: 35px;
      margin-bottom: 15px;
      padding-bottom: 10px;
      border-bottom: 2px solid var(--gray-200);
    }

    h3 {
        color: var(--primary-dark);
        font-size: 1.1rem;
        margin-top: 20px;
        margin-bottom: 10px;
    }

    /* --- Alert/Flash Messages --- */
    .flash-message { /* Common base class */
      padding: 12px 16px;
      border-radius: 12px; /* Rounded corners */
      margin-bottom: 20px;
      border-left-width: 4px;
      border-left-style: solid;
      opacity: 1; /* Start visible for JS transition */
      box-shadow: 0 2px 5px rgba(0, 0, 0, 0.05); /* Subtle shadow */
    }

    .error {
      background-color: var(--danger-bg);
      color: var(--danger);
      border-left-color: var(--danger);
    }

    .success {
      background-color: var(--success-bg);
      color: var(--success);
      border-left-color: var(--success);
    }

    .info {
      background-color: var(--info-bg);
      color: var(--info);
      border-left-color: var(--info);
    }

    /* --- Form Styling --- */
    .form-group {
      margin-bottom: 24px;
    }

    label {
      display: block;
      margin-bottom: 10px; /* More space below label */
      font-weight: 600;
      color: var(--gray-600);
      font-size: 0.95rem; /* Slightly larger label */
    }

    input[type=file], input[type=number], select {
      display: block;
      box-sizing: border-box;
      width: 100%;
      padding: 12px 16px; /* Increased padding */
      font-size: 1rem;
      border: 1px solid var(--gray-300);
      border-radius: 12px; /* More rounded corners */
      background-color: white;
      transition: border-color 0.15s ease-in-out, box-shadow 0.15s ease-in-out;
      color: var(--gray-800);
    }
    /* Style file input button */
    input[type=file]::file-selector-button {
        background: var(--gradient-button); /* Gradient background */
        color: white;
        border: none;
        padding: 8px 14px; /* Adjusted padding */
        border-radius: 8px; /* Rounded corners */
        cursor: pointer;
        margin-right: 12px; /* Space after button */
        transition: opacity 0.15s ease-in-out;
        font-weight: 600;
    }
    input[type=file]::file-selector-button:hover {
        opacity: 0.9; /* Slight fade on hover */
    }


    input[type=file]:focus, input[type=number]:focus, select:focus {
      outline: none;
      border-color: var(--primary-light); /* Lighter blue focus border */
      box-shadow: 0 0 0 3px rgba(0, 71, 160, 0.2); /* Adjusted focus shadow */
    }

    /* --- Buttons --- */
    button, input[type=submit] {
      background: var(--gradient-button); /* Gradient background */
      color: white;
      border: none;
      border-radius: 12px; /* Rounded corners */
      padding: 14px 20px; /* Larger padding */
      font-size: 1rem;
      font-weight: 600;
      cursor: pointer;
      width: 100%;
      transition: all 0.15s ease-in-out;
      text-align: center;
      display: inline-block;
      box-shadow: 0 2px 5px rgba(0, 71, 160, 0.2); /* Base shadow */
    }

    button:hover, input[type=submit]:hover {
      box-shadow: 0 4px 10px rgba(0, 71, 160, 0.3); /* Enhanced hover shadow */
      transform: translateY(-1px); /* Slight lift on hover */
    }
    button:active, input[type=submit]:active {
      transform: translateY(1px); /* Push down on click */
      box-shadow: 0 1px 3px rgba(0, 71, 160, 0.2); /* Reduced shadow on click */
    }


    button:disabled, input[type=submit]:disabled {
        opacity: 0.6;
        cursor: not-allowed;
        transform: none; /* Disable transforms */
        box-shadow: none; /* Remove shadow */
    }

    .btn-secondary {
      background: linear-gradient(135deg, var(--secondary-dark) 0%, var(--secondary) 100%); /* Green gradient */
    }
    .btn-secondary:hover {
      box-shadow: 0 4px 10px rgba(22, 163, 74, 0.3); /* Green hover shadow */
    }


    .btn-link { /* Simple link styling */
        color: var(--primary);
        text-decoration: none;
        background: none;
        border: none;
        padding: 0;
        font: inherit;
        cursor: pointer;
    }
    .btn-link:hover {
        text-decoration: underline;
        color: var(--primary-dark);
    }

    /* --- Progress Stepper --- */
    .stepper {
      display: flex;
      margin-bottom: 40px;
      padding-bottom: 20px;
      border-bottom: 1px solid var(--gray-200);
      justify-content: space-around;
      list-style: none;
      padding-left: 0;
      counter-reset: step-counter;
    }

    .step {
      flex: 1;
      text-align: center;
      position: relative;
    }

    /* Line connector */
    .step:not(:last-child)::after {
      content: '';
      position: absolute;
      top: 15px; /* Position line vertically centered with number */
      left: 50%; /* Start line from center of step */
      width: 100%;
      height: 2px;
      background-color: var(--gray-300);
      z-index: 1; /* Behind the number */
      transform: translateX(calc(18px)); /* Adjusted offset slightly past larger number */
    }
    /* Line color for completed steps */
    .step.completed:not(:last-child)::after {
        background-color: var(--primary); /* Use primary blue for completed line */
    }
    /* Adjust last step's connector */
    .step:last-child::after {
        display: none; /* No line after the last step */
    }


    .step-number {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      width: 36px; /* Larger step number */
      height: 36px;
      border-radius: 50%;
      background-color: var(--gray-300);
      color: white;
      font-weight: 600;
      margin-bottom: 8px;
      position: relative; /* Ensure it's above the line */
      z-index: 2;
      border: 2px solid white; /* Add border to lift it visually */
      box-shadow: 0 1px 5px rgba(0,0,0,0.1); /* Subtle shadow */
    }

    .step.active .step-number {
      background: var(--gradient-button); /* Gradient for active step */
      border-color: rgba(255, 255, 255, 0.7); /* Slightly transparent border */
      box-shadow: 0 0 0 3px rgba(0, 71, 160, 0.2); /* Focus ring */
    }

    .step.completed .step-number {
      background-color: var(--primary); /* Primary blue for completed */
      border-color: rgba(255, 255, 255, 0.7);
    }
    /* Add checkmark for completed steps */
    .step.completed .step-number::before {
        content: '✔';
        font-size: 16px;
        color: white;
    }

    .step-label {
      display: block; /* Ensure label is block */
      font-size: 0.95rem; /* Slightly larger label */
      color: var(--gray-600);
    }

    .step.active .step-label {
      color: var(--primary);
      font-weight: 600;
    }
    .step.completed .step-label {
      color: var(--primary); /* Use primary blue for completed label too */
      font-weight: 500;
    }


    /* --- Card Components (Used in Results) --- */
    .card {
      background-color: white;
      border-radius: 12px; /* Consistent rounded corners */
      box-shadow: var(--card-shadow);
      margin-bottom: 28px; /* Increased spacing */
      overflow: hidden; /* Ensure content respects border radius */
      border: 1px solid var(--gray-200); /* Subtle border */
      transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .card:hover {
        transform: translateY(-2px); /* Lift effect on hover */
        box-shadow: 0 8px 16px -4px rgba(0, 71, 160, 0.15); /* Enhanced hover shadow */
    }


    .card-header {
      /* background-color: var(--gray-100); */
      background: linear-gradient(to right, var(--primary-light), var(--primary)); /* Gradient header */
      padding: 16px 20px;
      font-weight: 600;
      border-bottom: 1px solid var(--gray-200); /* Keep separator */
      color: white; /* White text on gradient */
    }

    .card-body {
      padding: 22px; /* Slightly more padding */
    }
    .card-footer {
      background-color: var(--gray-100);
      padding: 14px 20px;
      border-top: 1px solid var(--gray-200);
      font-size: 0.9rem;
      color: var(--gray-600);
    }

    /* --- Tax Form Summary Styling (Results Page) --- */
    .tax-summary { /* Use card styling */
      margin-bottom: 30px;
    }

    .tax-heading { /* Use card-header */
      font-size: 1.25rem; /* Adjusted size */
    }

    .tax-line {
      display: flex;
      justify-content: space-between;
      align-items: center; /* Align items vertically */
      padding: 14px 0; /* Increased padding */
      border-bottom: 1px dashed var(--gray-200); /* Lighter dash */
      flex-wrap: wrap; /* Allow wrapping on small screens */
    }

    .tax-line:last-child {
      border-bottom: none;
      padding-bottom: 0;
    }

    .tax-label {
      font-weight: 500;
      color: var(--gray-600);
      flex-basis: 65%; /* Allocate space */
      padding-right: 10px; /* Space between label and value */
    }

    .tax-value {
      font-family: "SFMono-Regular", Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace; /* Monospace font */
      font-size: 1.1rem;
      font-weight: 600;
      text-align: right;
      flex-basis: 35%; /* Allocate space */
      background: rgba(0,0,0,0.03); /* Subtle background for value */
      padding: 6px 12px;
      border-radius: 6px;
    }

    .tax-value.gain {
      color: var(--success);
      background: rgba(22, 163, 74, 0.05); /* Light green background for gain */
    }

    .tax-value.loss {
      color: var(--danger);
      background: rgba(220, 38, 38, 0.05); /* Light red background for loss */
    }

    .tax-note {
      margin-top: 18px; /* Increased margin */
      font-size: 0.9rem; /* Slightly larger note */
      color: var(--gray-600);
      background-color: var(--warning-bg); /* Warning background */
      padding: 14px 18px; /* More padding */
      border-radius: 10px; /* Rounded corners */
      border-left: 4px solid var(--warning); /* Warning border */
      position: relative; /* For potential future icon */
    }
    .tax-note strong {
        color: var(--warning); /* Make strong text use warning color */
    }


    /* --- Statistics Display (Results Page) --- */
    .stats-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); /* Adjust minmax */
      gap: 18px; /* Increased gap */
      margin-top: 12px; /* Reduced margin */
    }

    .stat-card { /* Simpler styling than full card */
      background-color: white; /* White background for stat cards */
      border-radius: 10px; /* Rounded corners */
      padding: 18px; /* Increased padding */
      border: 1px solid var(--gray-200);
      box-shadow: 0 2px 8px rgba(0,0,0,0.03); /* Lighter shadow */
      transition: transform 0.2s ease;
    }
    .stat-card:hover {
        transform: translateY(-3px); /* Lift on hover */
        box-shadow: 0 4px 12px rgba(0,0,0,0.08); /* Enhanced shadow */
    }


    .stat-name {
      color: var(--gray-600);
      font-size: 0.875rem;
      margin-bottom: 8px; /* Increased space */
      display: block; /* Ensure it takes full width */
      font-weight: 500;
    }

    .stat-value {
      font-size: 1.4rem; /* Adjusted size */
      font-weight: 700; /* Bolder value */
      color: var(--primary-dark); /* Use dark blue for default stat value */
      display: block; /* Ensure it takes full width */
      word-wrap: break-word; /* Prevent overflow */
    }

    /* Specific value coloring */
    .stat-value.positive {
      color: var(--success);
    }
    .stat-value.negative {
      color: var(--danger);
    }


    /* Reward Breakdown List */
    .reward-breakdown-list {
        list-style: none;
        padding-left: 0;
        margin-top: 18px; /* Space above list */
        background: var(--gray-100); /* Light background for list area */
        border-radius: 10px;
        padding: 12px; /* Padding around list items */
    }
    .reward-breakdown-item {
        display: flex;
        justify-content: space-between;
        font-size: 0.9rem;
        padding: 8px 12px; /* Padding for each item */
        border-bottom: 1px dashed var(--gray-200);
        border-radius: 6px; /* Rounded corners for items */
        transition: background-color 0.15s ease;
    }
    .reward-breakdown-item:hover {
        background-color: rgba(255, 255, 255, 0.7); /* Subtle hover highlight */
    }

    .reward-breakdown-item:last-child {
        border-bottom: none;
    }
    .reward-type {
        color: var(--gray-600);
        font-weight: 500;
    }
    .reward-details {
        font-weight: 600; /* Slightly bolder details */
        font-family: monospace;
        color: var(--primary-dark); /* Dark blue for reward value */
    }


    /* --- Collapsible Sections (Details) --- */
    details {
      margin-bottom: 18px; /* Increased space */
      border-radius: 12px; /* Rounded corners */
      overflow: hidden; /* Important for border-radius */
      border: 1px solid var(--gray-200);
      background-color: white; /* Background for content area */
      box-shadow: 0 2px 8px rgba(0,0,0,0.03); /* Subtle shadow */
    }

    details > summary {
      padding: 16px 20px 16px 44px; /* Adjusted padding for custom marker */
      /* background-color: var(--gray-100); */
      background: linear-gradient(to right, rgba(0, 71, 160, 0.02), rgba(0, 71, 160, 0.08)); /* Subtle blue gradient */
      cursor: pointer;
      font-weight: 600;
      color: var(--primary-dark);
      list-style: none; /* Remove default marker */
      position: relative;
      transition: background-color 0.2s ease;
      border-bottom: 1px solid var(--gray-200); /* Separator line */
    }
    details > summary::-webkit-details-marker { display: none; } /* Hide marker in Chrome/Safari */
    details > summary::before { /* Custom marker */
        content: '►';
        position: absolute;
        left: 20px;
        top: 50%;
        transform: translateY(-50%);
        font-size: 0.8em;
        transition: transform 0.2s ease;
        color: var(--primary);
    }


    details[open] > summary {
      /* background-color: var(--gray-200); */
      background: linear-gradient(to right, rgba(0, 71, 160, 0.08), rgba(0, 71, 160, 0.15)); /* Darker gradient when open */
      border-bottom-color: var(--gray-300); /* Darker border when open */
    }
    details[open] > summary::before {
        transform: translateY(-50%) rotate(90deg);
    }


    details > .details-content { /* Wrapper for content inside details */
      padding: 18px; /* Increased padding */
      border-top: 1px solid var(--gray-200); /* Line between summary and content */
    }
    details[open] > .details-content {
        animation: fadeIn 0.3s ease-in; /* Fade in content */
    }


    /* --- Table Improvements --- */
    .table-container { /* Optional: for horizontal scrolling on small screens */
        overflow-x: auto;
        -webkit-overflow-scrolling: touch; /* Smooth scrolling on iOS */
        border-radius: 8px; /* Rounded corners for the scroll container */
        box-shadow: inset 0 0 0 1px var(--gray-200); /* Inner border */
    }

    table {
      width: 100%;
      border-collapse: separate; /* Use separate for border-spacing */
      border-spacing: 0;
      margin: 0; /* Remove default margins */
      font-size: 0.9rem; /* Base table font size */
    }

    th {
      /* background-color: var(--gray-100); */
      background: linear-gradient(to bottom, var(--gray-100), var(--gray-200)); /* Subtle gradient header */
      font-weight: 600;
      text-align: left;
      padding: 14px 12px; /* Adjusted padding */
      border-bottom: 2px solid var(--primary-light); /* Use light blue border */
      color: var(--primary-dark); /* Header text color */
      white-space: nowrap; /* Prevent header text wrapping */
      position: sticky; /* Sticky header for scrolling tables */
      top: 0; /* Stick to top */
      z-index: 1; /* Ensure header is above rows */
    }

    td {
      padding: 12px; /* Adjusted padding */
      border-bottom: 1px solid var(--gray-200);
      vertical-align: middle; /* Align cell content vertically */
      font-family: "SFMono-Regular", Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace; /* Monospace for data */
      font-size: 0.85rem; /* Slightly smaller data font */
    }
    td.numeric { /* Align numeric data right */
        text-align: right;
        font-feature-settings: "tnum"; /* Tabular nums for alignment */
        letter-spacing: -0.5px; /* Tighten spacing slightly */
    }
    td.gain {
        color: var(--success);
        font-weight: 500;
    }
    td.loss {
        color: var(--danger);
        font-weight: 500;
    }


    tr:hover {
      background-color: rgba(0, 71, 160, 0.03); /* Very subtle blue hover */
    }

    tr:last-child td {
      border-bottom: none; /* Remove border from last row */
    }

    /* --- Loading States & Transitions --- */
    .loading {
      display: none; /* Hidden by default */
      text-align: center;
      padding: 24px 0; /* Increased padding */
      margin: 24px 0;
    }

    .loading.active {
      display: block; /* Shown when active class is added */
    }

    .spinner {
      display: inline-block;
      width: 38px; /* Larger spinner */
      height: 38px;
      border: 3px solid rgba(0, 71, 160, 0.2); /* Lighter base border */
      border-radius: 50%;
      border-top-color: var(--primary); /* Primary blue spinner color */
      animation: spin 0.8s linear infinite; /* Faster spin */
    }

    @keyframes spin {
      to { transform: rotate(360deg); }
    }

    /* Page/content transitions */
    .fade-in {
      animation: fadeIn 0.4s ease-in-out; /* Slightly longer fade */
    }

    @keyframes fadeIn {
      from { opacity: 0; transform: translateY(10px); } /* Add subtle slide up */
      to { opacity: 1; transform: translateY(0); }
    }

    /* Button loading state */
    .btn-loading {
      position: relative;
      color: transparent !important; /* Hide text reliably */
      pointer-events: none; /* Prevent clicking while loading */
    }

    .btn-loading::after {
      content: "";
      position: absolute;
      /* Center the spinner */
      left: calc(50% - 10px); /* Adjust based on spinner size */
      top: calc(50% - 10px); /* Adjust based on spinner size */
      width: 20px; /* Spinner size */
      height: 20px;
      border: 2px solid rgba(255, 255, 255, 0.5); /* Spinner track */
      border-radius: 50%;
      border-top-color: white; /* Spinner color */
      animation: spin 0.8s linear infinite;
    }

    /* --- Responsive Adjustments --- */
    @media (max-width: 768px) {
      .container {
        margin: 20px;
        padding: 24px; /* Adjusted padding */
        border-radius: 12px; /* Consistent radius */
      }

      h1 { font-size: 1.6rem; }
      h2 { font-size: 1.3rem; }

      .app-header {
          flex-direction: column;
          align-items: flex-start;
          gap: 15px;
      }
      .main-nav {
          width: 100%;
          justify-content: flex-start; /* Align nav links left */
      }

      .tax-line {
          flex-direction: column;
          align-items: flex-start;
          gap: 5px; /* Add gap between label and value */
      }
      .tax-label, .tax-value {
          flex-basis: auto; /* Reset basis */
          width: 100%; /* Take full width */
          text-align: left; /* Align value left */
      }
      .tax-value { font-size: 1rem; }

      .stats-grid {
          grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); /* Smaller min width */
      }
      .stat-value { font-size: 1.2rem; }

      .footer-content {
          flex-direction: column;
          align-items: center;
          gap: 15px;
          text-align: center;
      }

      .stepper {
          flex-direction: column;
          align-items: flex-start;
          gap: 15px;
          border-bottom: none;
      }
      .step {
          width: 100%;
          text-align: left;
      }
      .step::after { display: none; } /* Hide connector lines on mobile */
      .step-number { margin-bottom: 4px; }
      .step-label { font-size: 1rem; }
    }

    /* For very small screens */
    @media (max-width: 480px) {
      .container {
        margin: 10px;
        padding: 16px;
        border-radius: 8px; /* Smaller radius */
      }

      h1 { font-size: 1.4rem; }
      h2 { font-size: 1.1rem; }

      .form-group { margin-bottom: 16px; }
      button, input[type=submit] { padding: 10px 16px; font-size: 0.9rem; border-radius: 8px; }
      input[type=file], input[type=number], select { border-radius: 8px; }


      .logo-text { font-size: 1rem; }
      .nav-link { padding: 6px 8px; font-size: 0.9rem; }

      .footer-content, .footer-links a { font-size: 0.8rem; }

      /* Further reduce table font size if needed */
      table, td, th { font-size: 0.8rem; padding: 8px 6px; }
      td.numeric { font-size: 0.8rem; }

      .stat-value { font-size: 1.1rem; }
    }
</style>
"""

# --- Embedded JavaScript ---
EMBEDDED_JS = """
<script>
    // static/js/main.js

    document.addEventListener('DOMContentLoaded', function() {

      // --- Add loading state to forms ---
      const forms = document.querySelectorAll('form');
      forms.forEach(form => {
        form.addEventListener('submit', function(event) {
          // Find the submit button within *this* specific form
          const submitBtn = form.querySelector('input[type="submit"], button[type="submit"]');

          if (submitBtn && !submitBtn.classList.contains('btn-loading')) {
            submitBtn.classList.add('btn-loading');
            submitBtn.disabled = true;

            // Find a loading indicator *associated* with this form if possible
            // (e.g., placed right after the form or button)
            // This example assumes a single global one '.loading' for simplicity
            const loadingEl = document.querySelector('.loading');
            if (loadingEl) {
              loadingEl.classList.add('active');
            }
          }
          // Prevent double submission if already loading
          else if (submitBtn && submitBtn.classList.contains('btn-loading')) {
              console.log("Form already submitting...");
              event.preventDefault(); // Stop the second submission
          }
        });
      });

      // --- Auto-hide flash messages after 5 seconds ---
      const flashMessages = document.querySelectorAll('.flash-message'); // Target the base class
      flashMessages.forEach(message => {
        // Ensure message is initially visible before starting timeout
        message.style.opacity = '1';
        message.style.display = 'block'; // Or flex, grid etc. depending on layout

        setTimeout(() => {
          message.style.transition = 'opacity 0.5s ease-out, transform 0.5s ease-out'; // Add transform transition
          message.style.opacity = '0';
          message.style.transform = 'translateY(-10px)'; // Add subtle slide up effect

          // Remove from DOM after transition completes
          setTimeout(() => {
               if (message.parentNode) { // Check if it still exists
                   message.parentNode.removeChild(message);
               }
          }, 500); // Matches transition duration
        }, 5000); // 5 seconds delay
      });

      // --- Enhanced details elements ---
      const detailsElements = document.querySelectorAll('details');
      detailsElements.forEach(details => {
        const summary = details.querySelector('summary');
        //const content = details.querySelector('.details-content'); // Assuming content is wrapped

        // Optional: Smooth open/close animation (can be complex)
        // Basic toggle listener for scrolling
        details.addEventListener('toggle', function(event) {
          if (this.open) {
            // Scroll the summary into view smoothly
             // Add a small delay to allow the element to fully render open before scrolling
            setTimeout(() => {
                summary.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
            }, 100);
          }
        });
      });

      // --- Activate current navigation link (using Flask endpoint) ---
      const navLinks = document.querySelectorAll('.main-nav .nav-link');
      const currentEndpoint = "{{ request.endpoint }}"; // Get endpoint from Flask context

      navLinks.forEach(link => {
          const linkHref = link.getAttribute('href');
          let linkEndpoint = null;

          // Try to match href to known endpoints (adjust as needed)
          if (linkHref === "{{ url_for('index') }}") {
              linkEndpoint = 'index';
          } else if (linkHref === "#disclaimer-footer") {
              // Disclaimer is not a separate page/endpoint, so ignore for active state
              linkEndpoint = null;
          }
          // *** THE PROBLEMATIC LINES HAVE BEEN REMOVED FROM HERE ***

          if (linkEndpoint && linkEndpoint === currentEndpoint) {
              link.classList.add('active');
          } else {
              link.classList.remove('active'); // Ensure others are not active
          }
      });

    }); // End DOMContentLoaded
</script>
"""


# --- HTML TEMPLATES (Updated with new structure and CSS classes) ---

# Base structure common to all templates
HTML_BASE_START = f"""
<!doctype html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
    <title>{{{{ title }}}} - Quebec Crypto Tax Helper</title>
    {EMBEDDED_CSS}
    <link rel="icon" href="data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22><text y=%22.9em%22 font-size=%2290%22>₿</text></svg>">
</head>
<body>
    <div class="main-content"> <!-- Added for footer positioning -->
        <header class="app-header container"> <!-- Header inside container -->
            <a href="{{{{ url_for('index') }}}}" class="logo">
                <span class="logo-icon">₿</span>
                <span class="logo-text">Quebec Crypto Tax Helper</span>
            </a>
            <nav class="main-nav">
                <a href="{{{{ url_for('index') }}}}" class="nav-link {{{{'active' if request.endpoint == 'index' else ''}}}}">Home</a>
                <!-- Add more nav links if needed -->
                 <a href="#disclaimer-footer" class="nav-link">Disclaimer</a>
            </nav>
        </header>

        <div class="container fade-in"> <!-- Main content area -->
            <!-- Stepper -->
            <ol class="stepper">
                <li class="step {{{{'active' if step == 1 else ('completed' if step > 1 else '')}}}}">
                    <span class="step-number"></span>
                    <span class="step-label">1. Upload History</span>
                </li>
                <li class="step {{{{'active' if step == 2 else ('completed' if step > 2 else '')}}}}">
                    <span class="step-number"></span>
                    <span class="step-label">2. Select Year</span>
                </li>
                <li class="step {{{{'active' if step == 3 else ''}}}}">
                    <span class="step-number"></span>
                    <span class="step-label">3. View Report</span>
                </li>
            </ol>

            <h1>{{{{ heading }}}}</h1>

            <!-- Flash messages -->
            {{% with messages = get_flashed_messages(with_categories=true) %}}
              {{% if messages %}}
                {{% for category, message in messages %}}
                  <div class="flash-message {{{{ category }}}}">{{{{ message }}}}</div>
                {{% endfor %}}
              {{% endif %}}
            {{% endwith %}}

            <!-- Loading Indicator -->
            <div class="loading"><div class="spinner"></div></div>

            <!-- Page specific content goes here -->
"""

HTML_BASE_END = f"""
            <!-- End Page specific content -->
        </div> <!-- End container -->
    </div> <!-- End main-content -->

    <footer class="app-footer">
      <div class="footer-content">
        <p>© {{{{ current_year_footer }}}} Quebec Crypto Tax Helper</p>
        <div class="footer-links">
          <!-- <a href="#about">About</a> -->
          <!-- <a href="#privacy">Privacy</a> -->
          <a href="#disclaimer-footer">Disclaimer</a>
        </div>
      </div>
      <div class="container" style="padding-top: 10px; padding-bottom: 10px; margin-top:10px; font-size: 0.8rem; color: var(--gray-600); border-radius: 10px; background-color: var(--warning-bg); border-left: 4px solid var(--warning);" id="disclaimer-footer">
          <p><strong>Disclaimer:</strong> This tool is for informational and educational purposes only and provides a simplified calculation based on publicly available information regarding Quebec and Canadian tax rules for cryptocurrency as of late 2024. It requires a *complete* transaction history for potentially accurate Adjusted Cost Base (ACB) calculations. Tax laws are complex and subject to change. This tool does not constitute financial or tax advice. Calculations may not cover all transaction types or specific tax situations (e.g., superficial losses, specific business income rules). **Always consult a qualified Quebec tax professional** for advice tailored to your individual circumstances before making any tax filing decisions. Use of this tool is at your own risk.</p>
      </div>
    </footer>

    {EMBEDDED_JS}
</body>
</html>
"""

# --- Specific Page Templates ---

INDEX_HTML = HTML_BASE_START + """
            <p style="text-align: center; color: var(--gray-600); margin-bottom: 30px;">
                Upload your <strong>complete</strong> transaction history CSV file (English or French format from supported platforms like Shakepay). The tool will process the entire history to calculate accurate cost bases for tax reporting.
            </p>

            <form method="post" enctype="multipart/form-data" action="{{ url_for('upload_file') }}">
                <div class="form-group">
                    <label for="file">Select Full Transaction History CSV File:</label>
                    <input type="file" name="file" id="file" required accept=".csv">
                </div>
                <button type="submit">Upload and Process History</button>
            </form>
""" + HTML_BASE_END


SELECT_YEAR_HTML = HTML_BASE_START + """
            <div class="info flash-message"> <!-- Using flash-message style for consistency -->
                <p>Successfully processed transaction history from file: <strong>{{ filename }}</strong></p>
                <p style="font-size: 0.9em; margin-top: 5px;">Detected transaction year range: {{ min_year }} - {{ max_year }}</p>
            </div>

            <p style="text-align: center; color: var(--gray-600); margin-bottom: 30px;">
                Now, please select the specific tax year for which you want to generate the report.
            </p>

            <form method="post" action="{{ url_for('show_results') }}">
                 <div class="form-group">
                    <label for="tax_year">Select Tax Year or Option:</label>
                    <select name="tax_year" id="tax_year" required>
                        <option value="all" {{ 'selected' if default_year == 'all' else '' }}>All Years (Summary)</option>
                        {% for year in available_years %}
                            {% if year != 'all' %} {# Ensure 'all' isn't duplicated if passed in list #}
                            <option value="{{ year }}" {{ 'selected' if year == default_year else '' }}>{{ year }}</option>
                            {% endif %}
                        {% endfor %}
                    </select>
                </div>
                <button type="submit" class="btn-secondary">Generate Report</button>
            </form>

            <p style="margin-top: 30px; text-align: center;">
                <a href="{{ url_for('index') }}" class="btn-link">Upload a different file</a>
            </p>
""" + HTML_BASE_END


RESULTS_HTML = HTML_BASE_START + """
            <div class="info flash-message" style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px;">
                 <span>Report for Tax Year: <strong>{{ tax_year }}</strong></span>
                 <span>File: <strong>{{ filename }}</strong> ({{ summary_stats['total_transactions'] }} transactions processed)</span>
            </div>

            <!-- Update Year Form -->
            <form method="post" action="{{ url_for('show_results') }}" style="margin-bottom: 30px; display: flex; align-items: flex-end; gap: 15px; flex-wrap: wrap; background-color: var(--gray-100); padding: 15px; border-radius: 12px;">
                 <div class="form-group" style="margin-bottom: 0; flex-grow: 1;">
                     <label for="tax_year_select" style="margin-bottom: 5px;">View Report For:</label>
                     <select name="tax_year" id="tax_year_select" required style="width: auto; display: inline-block; padding: 8px 10px; min-width: 150px;">
                         <option value="all" {{ 'selected' if tax_year == 'all' else '' }}>All Years (Summary)</option>
                         {% for year in available_years_for_update %} {# Use a distinct variable name if needed #}
                             {% if year != 'all' %}
                             <option value="{{ year }}" {{ 'selected' if year|string == tax_year|string else '' }}>{{ year }}</option>
                             {% endif %}
                         {% endfor %}
                     </select>
                 </div>
                 <button type="submit" style="width: auto; padding: 9px 18px; margin-bottom: 0; flex-shrink: 0;">Update Report</button>
                 <a href="{{ url_for('index') }}" class="btn-link" style="margin-bottom: 5px;">Upload New File</a>
            </form>

            <!-- Tax Form Summary Card -->
            {% if not is_all_years_report %} {# Only show TP form summary for single year reports #}
            <div class="card tax-summary">
                <div class="card-header tax-heading">TP-21.4.39-V Summary for {{ tax_year }}</div>
                <div class="card-body">
                    <div class="tax-line">
                         <span class="tax-label">Part 4.1 - Line 65: Capital gains/(losses) <strong>before June 25, {{ tax_year + 1 }}</strong>:</span>
                         <span class="tax-value {{ 'loss' if tax_summary['before_cutoff'] < 0 else 'gain' }}">{{ tax_summary['before_cutoff'] | currency }}</span>
                    </div>
                     <div class="tax-line">
                         <span class="tax-label">Part 4.2 - Line 98: Capital gains/(losses) <strong>on or after June 25, {{ tax_year + 1 }}</strong>:</span>
                         <span class="tax-value {{ 'loss' if tax_summary['after_cutoff'] < 0 else 'gain' }}">{{ tax_summary['after_cutoff'] | currency }}</span>
                    </div>
                    <div class="tax-line">
                         <span class="tax-label">Part 6.2 - Line 135: Interest income (Rewards/Cashback):</span>
                         <span class="tax-value gain">{{ tax_summary['reward_income'] | currency }}</span>
                    </div>
                    <p class="tax-note">
                        <strong>Important:</strong> Enter these calculated amounts on the corresponding lines of form TP-21.4.39-V for tax year <strong>{{ tax_year }}</strong>. Follow form instructions for subsequent calculations. Consult a tax professional to confirm.
                    </p>
                </div>
            </div>
            {% else %} {# Show aggregated summary for "All Years" report #}
            <div class="card tax-summary">
                <div class="card-header tax-heading">Aggregated Summary for {{ min_year }} - {{ max_year }}</div>
                <div class="card-body">
                    <div class="tax-line">
                         <span class="tax-label">Total Capital Gains/(Losses) ({{ min_year }}-{{ max_year }}):</span>
                         <span class="tax-value {{ 'loss' if aggregated_summary['total_gain_loss'] < 0 else 'gain' }}">{{ aggregated_summary['total_gain_loss'] | currency }}</span>
                    </div>
                    <div class="tax-line">
                         <span class="tax-label">Total Reward Income ({{ min_year }}-{{ max_year }}):</span>
                         <span class="tax-value gain">{{ aggregated_summary['total_reward_income'] | currency }}</span>
                    </div>
                    <p class="tax-note">
                        <strong>Note:</strong> This is an aggregated summary across all years. Specific form lines apply only to individual tax years. Consult a tax professional for filing.
                    </p>
                </div>
            </div>
            {% endif %}

            <!-- Statistics Card -->
            <div class="card">
                <div class="card-header">Statistics for {{ 'Tax Year ' + tax_year|string if not is_all_years_report else 'All Years (' + min_year|string + '-' + max_year|string + ')' }}</div>
                <div class="card-body">
                    {% set stats = year_stats if not is_all_years_report else aggregated_stats %}
                    <div class="stats-grid">
                        <div class="stat-card">
                            <span class="stat-name">Total Dispositions</span>
                            <span class="stat-value">{{ stats['disposition_count'] }}</span>
                        </div>
                        <div class="stat-card">
                            <span class="stat-name">Total Proceeds:</span>
                            <span class="stat-value">{{ stats['total_proceeds'] | currency }}</span>
                        </div>
                        <div class="stat-card">
                            <span class="stat-name">Total Cost Base:</span>
                            <span class="stat-value">{{ stats['total_cost_disposed'] | currency }}</span>
                        </div>
                         {% if not is_all_years_report %} {# Avg Gain/Loss only for single year #}
                         <div class="stat-card">
                            <span class="stat-name">Average Gain/Loss:</span>
                            <span class="stat-value {{ 'negative' if stats['avg_gain_loss'] < 0 else 'positive' }}">{{ stats['avg_gain_loss'] | currency }}</span>
                         </div>
                         {% else %} {# Show Total Gain/Loss for all years #}
                         <div class="stat-card">
                            <span class="stat-name">Total Gain/Loss (CAD)</span>
                            {# Note: Aggregated Gain/Loss still uses old format as it's handled in the Aggregated Summary card #}
                            <span class="stat-value {{ 'negative' if aggregated_summary['total_gain_loss'] < 0 else 'positive' }}">{{ "%.2f"|format(aggregated_summary['total_gain_loss']) }}</span>
                         </div>
                         {% endif %}
                        <div class="stat-card">
                            <span class="stat-name">Largest Gain:</span>
                            <span class="stat-value positive">{{ stats['largest_gain'] | currency }}</span>
                        </div>
                        <div class="stat-card">
                            <span class="stat-name">Largest Loss:</span>
                            <span class="stat-value negative">{{ stats['largest_loss'] | currency }}</span>
                        </div>
                         <div class="stat-card">
                            <span class="stat-name">Reward Transactions:</span>
                            <span class="stat-value">{{ stats['reward_count'] }}</span>
                        </div>
                         <div class="stat-card">
                            <span class="stat-name">Total Reward Income:</span>
                            {# Use appropriate variable based on report type #}
                            <span class="stat-value positive">{{ (aggregated_summary['total_reward_income'] if is_all_years_report else tax_summary['reward_income']) | currency }}</span>
                        </div>
                    </div>
                    <!-- Reward Breakdown -->
                    {% if stats['reward_breakdown'] %}
                        <h3 style="margin-top: 25px;">Reward Breakdown:</h3>
                        <ul class="reward-breakdown-list">
                        {% for type, data in stats['reward_breakdown'].items()|sort %}
                            <li class="reward-breakdown-item">
                                <span class="reward-type">{{ type }}:</span>
                                <span class="reward-details">{{ data['count'] }} transactions, {{ data['value'] | currency }}</span>
                            </li>
                        {% endfor %}
                        </ul>
                    {% endif %}
                </div>
            </div>

            <!-- Detailed Transactions (Only show for single year reports) -->
            {% if not is_all_years_report %}
            <h2>Transaction Details for {{ tax_year }}</h2>
            <details>
                <summary>Dispositions: {{ year_stats['disposition_count'] }}</summary>
                <div class="details-content">
                    {% if dispositions_in_year %}
                    <div class="table-container">
                    <table>
                        <thead>
                            <tr>
                                <th>Date</th>
                                <th>Asset</th>
                                <th style="text-align: right;">Amount</th>
                                <th style="text-align: right;">Proceeds (CAD)</th>
                                <th style="text-align: right;">Cost Base (CAD)</th>
                                <th style="text-align: right;">Gain/(Loss) (CAD)</th>
                                <th>Period</th>
                             </tr>
                        </thead>
                        <tbody>
                            {% for tx in dispositions_in_year %}
                            <tr>
                                <td>{{ tx.date.strftime('%Y-%m-%d %H:%M') if tx.date else 'N/A' }}</td>
                                <td>{{ tx.asset }}</td>
                                <td class="numeric">{{ "%.8f"|format(tx.amount) }}</td>
                                <td class="numeric">{{ "%.2f"|format(tx.proceeds) }}</td>
                                <td class="numeric">{{ "%.2f"|format(tx.cost_base) }}</td>
                                <td class="numeric {{ 'loss' if tx.gain_loss < 0 else 'gain' }}">{{ "%.2f"|format(tx.gain_loss) }}</td>
                                <td>{{ tx.period.replace('_cutoff', '')|capitalize if tx.period else 'N/A' }}</td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                    </div>
                    {% else %}
                    <p>No disposition transactions found for this year.</p>
                    {% endif %}
                </div>
            </details>

            <details>
                <summary>Rewards: {{ year_stats['reward_count'] }}</summary>
                 <div class="details-content">
                     {% if rewards_in_year %}
                     <div class="table-container">
                     <table>
                        <thead>
                            <tr>
                                <th>Date</th>
                                <th>Asset</th>
                                <th style="text-align: right;">Amount</th>
                                <th style="text-align: right;">Income (CAD)</th>
                                <th>Description</th>
                             </tr>
                        </thead>
                        <tbody>
                            {% for tx in rewards_in_year %}
                            <tr>
                                <td>{{ tx.date.strftime('%Y-%m-%d %H:%M') if tx.date else 'N/A' }}</td>
                                <td>{{ tx.asset }}</td>
                                <td class="numeric">{{ "%.8f"|format(tx.amount) }}</td>
                                <td class="numeric gain">{{ "%.2f"|format(tx.income) }}</td>
                                <td>{{ tx.description }}</td>
                            </tr>
                            {% endfor %}
                        </tbody>
                     </table>
                     </div>
                     {% else %}
                     <p>No reward transactions found for this year.</p>
                     {% endif %}
                 </div>
            </details>
            {% else %}
            <h2>Transaction Details</h2>
            <p class="info flash-message">Detailed transaction lists are not shown in the 'All Years' summary view. Please select an individual year to see detailed transactions.</p>
            {% endif %}
""" + HTML_BASE_END


# --- Flask App Setup (Identical Backend Logic) ---
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
app.secret_key = os.urandom(32)

app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_USE_SIGNER'] = True
app.config['SESSION_FILE_DIR'] = './.flask_session/'
Session(app)

# Create directories if they don't exist
if not os.path.exists(app.config['SESSION_FILE_DIR']):
    try:
        os.makedirs(app.config['SESSION_FILE_DIR'])
    except OSError as e:
        print(f"Error creating session directory: {e}")

if not os.path.exists(app.config['UPLOAD_FOLDER']):
    try:
        os.makedirs(app.config['UPLOAD_FOLDER'])
    except OSError as e:
        print(f"Error creating upload directory: {e}")

# --- Helper Functions (Identical) ---
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def quantize_decimal(value, places=DECIMAL_PLACES):
    if value is None: return Decimal(0)
    if not isinstance(value, Decimal):
        try: value = Decimal(str(value))
        except (TypeError, ValueError, InvalidOperation): return Decimal(0)
    rounding_precision = Decimal('1e-' + str(places))
    return value.quantize(rounding_precision, rounding=ROUND_HALF_UP)

def parse_decimal_french(value_str):
    if isinstance(value_str, (int, float, Decimal)): return Decimal(value_str)
    if not isinstance(value_str, str): return Decimal(0)
    cleaned_value = value_str.strip().replace(',', '.')
    if not cleaned_value: return Decimal(0)
    try: return Decimal(cleaned_value)
    except InvalidOperation: return Decimal(0)

# --- Custom Jinja Filter for Currency Formatting ---
def format_currency(value):
    try:
        # Ensure value is a Decimal
        if not isinstance(value, Decimal):
            value = Decimal(str(value))

        # Quantize to 2 decimal places
        value = quantize_decimal(value, CURRENCY_PLACES)

        # Determine sign and format
        prefix = '–$ ' if value < 0 else '$ '
        formatted_value = "{:,.2f}".format(abs(value)) # Comma separator, 2 decimals

        return prefix + formatted_value
    except (TypeError, ValueError, InvalidOperation):
        return "$ 0.00" # Default fallback

# Register the custom filter
@app.template_filter('currency')
def currency_filter(value):
    return format_currency(value)

# --- Core Processing Logic (Identical) ---
def process_full_history(filepath):
    all_taxable_events = []
    total_processed_rows = 0
    min_year = None
    max_year = None
    try:
        with open(filepath, 'r', encoding='utf-8-sig') as f:
            header_line = f.readline().strip()
            is_french = '"Montant crédité"' in header_line or '"Actif crédité"' in header_line or 'Montant crédité' in header_line
        df = pd.read_csv(filepath, dtype=str, keep_default_na=False, encoding='utf-8-sig')
        total_processed_rows = len(df)
        if is_french:
            print("French format detected.")
            missing_french_cols = [fr_col for fr_col in FRENCH_TO_ENGLISH_MAP.keys() if fr_col not in df.columns]
            essential_french = ["Date", "Type", "Montant débité", "Actif débité", "Montant crédité", "Actif crédité", "Valeur du marché"]
            truly_missing = [col for col in essential_french if col in missing_french_cols]
            if truly_missing: raise ValueError(f"Essential CSV columns missing (French): {', '.join(truly_missing)}")
            elif missing_french_cols: print(f"Warning: Optional French columns missing: {', '.join(missing_french_cols)}")
            df.rename(columns=FRENCH_TO_ENGLISH_MAP, inplace=True)
            if 'Type' in df.columns: df['Type'] = df['Type'].replace(FRENCH_TO_ENGLISH_TYPES)
            elif 'Type' not in df.columns: raise ValueError("Essential 'Type' column not found after attempting French mapping.")
        else: print("Assuming English format.")
        expected_columns = ['Date', 'Type', 'Amount Debited', 'Asset Debited', 'Amount Credited', 'Asset Credited', 'Market Value']
        missing_cols = [col for col in expected_columns if col not in df.columns]
        if missing_cols: raise ValueError(f"Essential CSV columns missing: {', '.join(missing_cols)}")
        if 'Book Cost' not in df.columns: df['Book Cost'] = '0'
        if 'Description' not in df.columns: df['Description'] = ''
        try: df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        except Exception as e: raise ValueError(f"Error parsing 'Date' column: {e}.")
        if df['Date'].isnull().all(): raise ValueError("No valid dates found in the 'Date' column.")
        num_bad_dates = df['Date'].isnull().sum()
        if num_bad_dates > 0: print(f"Warning: {num_bad_dates} row(s) had invalid dates and were skipped."); df.dropna(subset=['Date'], inplace=True)
        if df.empty: raise ValueError("CSV contains no valid transactions after handling invalid dates.")
        min_year = df['Date'].min().year
        max_year = df['Date'].max().year
        print(f"Detected transaction year range: {min_year} - {max_year}")
        financial_cols = ['Amount Debited', 'Amount Credited', 'Market Value', 'Book Cost']
        for col in financial_cols:
            try: df[col] = df[col].apply(parse_decimal_french)
            except Exception as e: raise ValueError(f"Unexpected error converting column '{col}' to Decimal: {e}")
        df['Asset Debited'] = df['Asset Debited'].fillna('').str.strip().str.upper()
        df['Asset Credited'] = df['Asset Credited'].fillna('').str.strip().str.upper()
        df['Description'] = df['Description'].fillna('')
        df.sort_values(by='Date', inplace=True)
        acb_data = {}
        cutoff_date = pd.Timestamp('2024-06-25 00:00:00')
        for index, row in df.iterrows():
            date=row['Date']; tx_type=row['Type']; asset_debited=row['Asset Debited']; amount_debited=quantize_decimal(row['Amount Debited'],DECIMAL_PLACES); asset_credited=row['Asset Credited']; amount_credited=quantize_decimal(row['Amount Credited'],DECIMAL_PLACES); market_value=quantize_decimal(row['Market Value'],CURRENCY_PLACES); book_cost=quantize_decimal(row['Book Cost'],CURRENCY_PLACES); description=row['Description']
            if tx_type in ['Buy','Reward','Receive'] and amount_credited > 0 and asset_credited:
                asset=asset_credited; amount=amount_credited
                value_at_receipt = market_value if market_value > 0 else book_cost
                if value_at_receipt <= 0:
                    if tx_type == 'Reward': print(f"Warning ({date}): Reward of {amount} {asset} has zero value. Assuming zero cost/income.")
                    else: print(f"Warning ({date}): Acquisition of {amount} {asset} has zero value. Assuming zero cost.")
                    value_at_receipt=Decimal(0)
                cost_for_acb=value_at_receipt
                if asset not in acb_data: acb_data[asset]={'quantity':Decimal(0),'total_cost':Decimal(0)}
                acb_data[asset]['quantity']+=amount; acb_data[asset]['total_cost']+=cost_for_acb
                if tx_type=='Reward': all_taxable_events.append({'date':date,'type':'reward','asset':asset,'amount':amount,'income':value_at_receipt,'description':description})
            elif (tx_type=='Sell' or (tx_type=='Send' and market_value > 0)) and amount_debited > 0 and asset_debited:
                asset=asset_debited; amount_disposed=amount_debited; proceeds=market_value
                if asset and amount_disposed > 0:
                    if asset not in acb_data or acb_data[asset]['quantity']<=Decimal('1e-12'): print(f"Warning ({date}): Disposition of {amount_disposed} {asset} but no prior ACB. Skipping."); continue
                    current_quantity=acb_data[asset]['quantity']; current_total_cost=acb_data[asset]['total_cost']
                    if amount_disposed > current_quantity+Decimal('1e-12'): print(f"Warning ({date}): Disposing {amount_disposed} {asset}, only {current_quantity} available. Adjusting."); amount_disposed=current_quantity
                    if current_quantity<=Decimal('1e-12'): print(f"Warning ({date}): Quantity of {asset} is zero. Skipping disposition."); continue
                    acb_per_unit=(current_total_cost/current_quantity) if current_quantity > 0 else Decimal(0)
                    cost_of_disposed=quantize_decimal(amount_disposed*acb_per_unit,CURRENCY_PLACES)
                    gain_loss=quantize_decimal(proceeds-cost_of_disposed,CURRENCY_PLACES)
                    period_flag='after_cutoff' if date >= cutoff_date else 'before_cutoff'
                    all_taxable_events.append({'date':date,'type':'disposition','asset':asset,'amount':amount_disposed,'proceeds':proceeds,'cost_base':cost_of_disposed,'gain_loss':gain_loss,'period':period_flag})
                    acb_data[asset]['quantity']-=amount_disposed; acb_data[asset]['total_cost']-=(amount_disposed*acb_per_unit)
                    if acb_data[asset]['quantity']<Decimal('1e-10'): acb_data[asset]['quantity']=Decimal(0); acb_data[asset]['total_cost']=Decimal(0)
                    elif acb_data[asset]['total_cost']<0: print(f"Warning ({date}): ACB cost for {asset} negative ({acb_data[asset]['total_cost']}), resetting to zero."); acb_data[asset]['total_cost']=Decimal(0)
        summary_stats={'total_transactions':total_processed_rows}
        return all_taxable_events, summary_stats, min_year, max_year
    except ValueError as ve: print(f"Data validation error: {ve}"); raise
    except FileNotFoundError: print(f"Error: Input file not found at {filepath}"); raise ValueError(f"Could not find the uploaded file.")
    except pd.errors.EmptyDataError: print("Error: CSV file is empty."); raise ValueError("Uploaded CSV is empty.")
    except Exception as e: print(f"Unexpected error in processing: {traceback.format_exc()}"); raise ValueError(f"Unexpected error during processing: {e}")

def calculate_report_for_year(all_taxable_events, tax_year):
    gains_losses = {'before_cutoff': Decimal(0), 'after_cutoff': Decimal(0)}; total_reward_income = Decimal(0)
    dispositions_in_year = []; rewards_in_year = []
    reward_stats = defaultdict(lambda: {'count': 0, 'value': Decimal(0)})
    disposition_count = 0; reward_count = 0; total_proceeds = Decimal(0); total_cost_disposed = Decimal(0)
    largest_gain = Decimal('-Infinity'); largest_loss = Decimal('Infinity'); assets_involved = set()
    for event in all_taxable_events:
        event_date = event.get('date')
        if not isinstance(event_date, pd.Timestamp): print(f"Skipping event due to invalid date type: {event}"); continue
        if event_date.year == tax_year:
            event_type = event.get('type')
            if event_type == 'disposition':
                disposition_count += 1; dispositions_in_year.append(event); assets_involved.add(event.get('asset','UNKNOWN'))
                proceeds=event.get('proceeds',Decimal(0)); cost_base=event.get('cost_base',Decimal(0)); gain_loss=event.get('gain_loss',Decimal(0)); period=event.get('period','unknown')
                total_proceeds+=proceeds; total_cost_disposed+=cost_base
                if period == 'before_cutoff': gains_losses['before_cutoff'] += gain_loss
                elif period == 'after_cutoff': gains_losses['after_cutoff'] += gain_loss
                else: print(f"Warning: Disposition on {event_date} has unknown period '{period}'. Assigning to after_cutoff."); gains_losses['after_cutoff']+=gain_loss
                if gain_loss > largest_gain: largest_gain = gain_loss
                if gain_loss < largest_loss: largest_loss = gain_loss
            elif event_type == 'reward':
                reward_count += 1; rewards_in_year.append(event); income = event.get('income', Decimal(0)); total_reward_income += income
                desc=event.get('description','Other Reward').lower(); category='Other Reward'
                if 'shakingsats' in desc: category='ShakingSats'
                elif 'cashback' in desc or 'remise' in desc: category='Cashback/Rebate'
                elif 'secretsats' in desc: category = 'SecretSats'
                reward_stats[category]['count'] += 1; reward_stats[category]['value'] += income
    avg_gain_loss = (gains_losses['before_cutoff'] + gains_losses['after_cutoff']) / disposition_count if disposition_count > 0 else Decimal(0)
    if largest_gain == Decimal('-Infinity'): largest_gain = Decimal(0)
    if largest_loss == Decimal('Infinity'): largest_loss = Decimal(0)
    tax_summary = {'before_cutoff': quantize_decimal(gains_losses['before_cutoff'], CURRENCY_PLACES), 'after_cutoff': quantize_decimal(gains_losses['after_cutoff'], CURRENCY_PLACES), 'reward_income': quantize_decimal(total_reward_income, CURRENCY_PLACES)}
    year_stats = {'disposition_count': disposition_count, 'reward_count': reward_count, 'total_proceeds': quantize_decimal(total_proceeds, CURRENCY_PLACES), 'total_cost_disposed': quantize_decimal(total_cost_disposed, CURRENCY_PLACES), 'avg_gain_loss': quantize_decimal(avg_gain_loss, CURRENCY_PLACES), 'largest_gain': quantize_decimal(largest_gain, CURRENCY_PLACES), 'largest_loss': quantize_decimal(largest_loss, CURRENCY_PLACES), 'reward_breakdown': {k: {'count': v['count'], 'value': quantize_decimal(v['value'], CURRENCY_PLACES)} for k, v in reward_stats.items()}, 'assets_involved': sorted(list(assets_involved))}
    dispositions_in_year.sort(key=lambda x: x.get('date', pd.Timestamp.min)); rewards_in_year.sort(key=lambda x: x.get('date', pd.Timestamp.min))
    return tax_summary, year_stats, dispositions_in_year, rewards_in_year


# --- Flask Routes ---
@app.route('/', methods=['GET'])
def index():
    session.pop('all_taxable_events', None); session.pop('original_filename', None); session.pop('summary_stats', None); session.pop('min_year', None); session.pop('max_year', None)
    print("Session cleared for new upload.")
    return render_template_string(INDEX_HTML, title="Upload CSV", heading="Upload Transaction History", step=1, current_year_footer=datetime.datetime.now().year)

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files: flash('No file part in the request.', 'error'); return redirect(url_for('index'))
    file = request.files['file']
    if file.filename == '': flash('No file selected for uploading.', 'error'); return redirect(url_for('index'))
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename + "_proctemp_" + str(os.getpid()))
        try:
            file.save(filepath); print(f"File saved temporarily to: {filepath}")
            # time.sleep(1) # Simulate processing
            all_taxable_events, summary_stats, min_year, max_year = process_full_history(filepath)
            print(f"Processing complete. Events: {len(all_taxable_events)}, Min Year: {min_year}, Max Year: {max_year}")
            serializable_events = []
            for event in all_taxable_events:
                 event_copy = event.copy()
                 if isinstance(event_copy.get('date'), pd.Timestamp): event_copy['date'] = event_copy['date'].isoformat()
                 for key in ['amount', 'income', 'proceeds', 'cost_base', 'gain_loss']:
                    if key in event_copy and isinstance(event_copy[key], Decimal): event_copy[key] = str(event_copy[key])
                 serializable_events.append(event_copy)
            session['all_taxable_events'] = serializable_events
            session['original_filename'] = filename
            session['summary_stats'] = summary_stats
            session['min_year'] = min_year
            session['max_year'] = max_year
            session.modified = True
            print(f"Data stored in session for filename: {filename}")
            flash('File processed successfully. Please select the tax year.', 'success')
            return redirect(url_for('select_year'))
        except ValueError as e: flash(f"Error processing file: {e}", 'error'); print(f"ValueError during processing: {e}")
        except Exception as e: print(f"Unexpected upload/processing error: {traceback.format_exc()}"); flash(f"An unexpected error occurred: {e}", 'error')
        finally:
            if os.path.exists(filepath):
                try: os.remove(filepath); print(f"Temporary file removed: {filepath}")
                except OSError as e: print(f"Warning: Could not remove temporary file {filepath}: {e}")
        return redirect(url_for('index'))
    else: flash('Invalid file type. Only CSV files are allowed.', 'error'); return redirect(url_for('index'))

@app.route('/select_year', methods=['GET'])
def select_year():
    if 'all_taxable_events' not in session or 'min_year' not in session or 'max_year' not in session:
        flash('Processed data not found in session. Please upload the file again.', 'error'); print("Session data missing for /select_year"); return redirect(url_for('index'))
    filename = session.get('original_filename', 'Unknown')
    min_year_data = session.get('min_year'); max_year_data = session.get('max_year'); current_year = datetime.datetime.now().year
    if min_year_data is None or max_year_data is None or not isinstance(min_year_data, int) or not isinstance(max_year_data, int):
         flash('Error retrieving year range from processed data. Try uploading again.', 'error'); print(f"Invalid min/max year in session: {min_year_data}, {max_year_data}"); session.pop('all_taxable_events',None); session.pop('min_year',None); session.pop('max_year',None); return redirect(url_for('index'))
    potential_default = max_year_data
    if potential_default > current_year: potential_default = current_year
    default_year = max(min_year_data, potential_default)
    default_year = min(max_year_data, default_year)

    # Generate list of available years for the dropdown
    available_years = list(range(min_year_data, max_year_data + 1))
    # available_years.insert(0, "all") # Add "all" option - handled in template now

    print(f"Rendering select_year page. Min: {min_year_data}, Max: {max_year_data}, Default: {default_year}, Available: {available_years}")
    return render_template_string(SELECT_YEAR_HTML, title="Select Tax Year", heading="Select Tax Year", step=2, filename=filename, min_year=min_year_data, max_year=max_year_data, default_year=default_year, available_years=available_years, current_year_footer=datetime.datetime.now().year)

@app.route('/results', methods=['POST'])
def show_results():
    if 'all_taxable_events' not in session or 'min_year' not in session or 'max_year' not in session:
        flash('Session data expired or missing. Please upload the file again.', 'error')
        print("Session data missing for /results")
        return redirect(url_for('index'))

    min_year_data = session.get('min_year')
    max_year_data = session.get('max_year')
    current_real_year = datetime.datetime.now().year

    if min_year_data is None or max_year_data is None or not isinstance(min_year_data, int) or not isinstance(max_year_data, int):
        flash('Error retrieving valid year range from session. Please upload again.', 'error')
        print(f"Invalid min/max year in session during results: {min_year_data}, {max_year_data}")
        return redirect(url_for('index'))

    tax_year_str = request.form.get('tax_year')
    if tax_year_str is None:
        flash("Tax year selection not provided.", 'error')
        return redirect(url_for('select_year'))

    is_all_years_report = (tax_year_str == 'all')
    tax_year_display = "All Years" if is_all_years_report else tax_year_str # For titles/headings

    if not is_all_years_report:
        try:
            tax_year = int(tax_year_str)
            if not (min_year_data <= tax_year <= max_year_data):
                raise ValueError(f"Selected year {tax_year} is outside the valid range ({min_year_data}-{max_year_data}).")
        except (TypeError, ValueError) as e:
            flash(f'Invalid tax year selection: {e}.', 'error')
            print(f"Invalid tax year received: {request.form.get('tax_year')}. Error: {e}")
            return redirect(url_for('select_year'))
    else:
        tax_year = "all" # Use 'all' internally for logic/selection state

    all_taxable_events_serial = session.get('all_taxable_events', [])
    filename = session.get('original_filename', 'Unknown')
    summary_stats_global = session.get('summary_stats', {'total_transactions': 'N/A'})

    if not all_taxable_events_serial:
        flash('Processed transaction data is empty in session. Please upload again.', 'error')
        print("all_taxable_events_serial was empty.")
        return redirect(url_for('index'))

    all_taxable_events = []
    try:
        for event_data in all_taxable_events_serial:
            event = event_data.copy()
            if 'date' in event and isinstance(event['date'], str):
                try: event['date'] = pd.Timestamp(event['date'])
                except ValueError: print(f"Warning: Could not parse date '{event['date']}'. Skipping."); continue
            numeric_fields = ['amount', 'income', 'proceeds', 'cost_base', 'gain_loss']
            for field in numeric_fields:
                if field in event and event[field] is not None:
                    try: event[field] = Decimal(str(event[field]))
                    except (InvalidOperation, TypeError): print(f"Warning: Could not convert '{event[field]}' to Decimal for '{field}'. Using 0."); event[field] = Decimal(0)
            all_taxable_events.append(event)
    except Exception as e:
        print(f"Error deserializing session data: {traceback.format_exc()}")
        flash('Error reading processed data. Please try uploading again.', 'error')
        return redirect(url_for('index'))

    if not all_taxable_events:
        flash('Failed to load valid transaction data. Please upload again.', 'error')
        print("all_taxable_events empty after deserialization.")
        return redirect(url_for('index'))

    # Generate available years for the update dropdown on the results page
    available_years_for_update = list(range(min_year_data, max_year_data + 1))

    try:
        if is_all_years_report:
            print(f"Calculating aggregated report for years: {min_year_data}-{max_year_data}")
            # Initialize aggregated data structures
            aggregated_summary = {'total_gain_loss': Decimal(0), 'total_reward_income': Decimal(0)}
            aggregated_stats = {
                'disposition_count': 0, 'reward_count': 0,
                'total_proceeds': Decimal(0), 'total_cost_disposed': Decimal(0),
                'largest_gain': Decimal('-Infinity'), 'largest_loss': Decimal('Infinity'),
                'reward_breakdown': defaultdict(lambda: {'count': 0, 'value': Decimal(0)}),
                'assets_involved': set()
            }

            # Loop through each year in the range
            for year in range(min_year_data, max_year_data + 1):
                year_summary, year_stats_single, _, _ = calculate_report_for_year(all_taxable_events, year)

                # Aggregate results
                aggregated_summary['total_gain_loss'] += (year_summary['before_cutoff'] + year_summary['after_cutoff'])
                aggregated_summary['total_reward_income'] += year_summary['reward_income']

                aggregated_stats['disposition_count'] += year_stats_single['disposition_count']
                aggregated_stats['reward_count'] += year_stats_single['reward_count']
                aggregated_stats['total_proceeds'] += year_stats_single['total_proceeds']
                aggregated_stats['total_cost_disposed'] += year_stats_single['total_cost_disposed']
                aggregated_stats['largest_gain'] = max(aggregated_stats['largest_gain'], year_stats_single['largest_gain'])
                aggregated_stats['largest_loss'] = min(aggregated_stats['largest_loss'], year_stats_single['largest_loss'])
                aggregated_stats['assets_involved'].update(year_stats_single['assets_involved'])

                for reward_type, data in year_stats_single['reward_breakdown'].items():
                    aggregated_stats['reward_breakdown'][reward_type]['count'] += data['count']
                    aggregated_stats['reward_breakdown'][reward_type]['value'] += data['value']

            # Finalize aggregated stats
            if aggregated_stats['largest_gain'] == Decimal('-Infinity'): aggregated_stats['largest_gain'] = Decimal(0)
            if aggregated_stats['largest_loss'] == Decimal('Infinity'): aggregated_stats['largest_loss'] = Decimal(0)
            aggregated_stats['assets_involved'] = sorted(list(aggregated_stats['assets_involved']))
            aggregated_stats['reward_breakdown'] = {k: {'count': v['count'], 'value': quantize_decimal(v['value'], CURRENCY_PLACES)} for k, v in aggregated_stats['reward_breakdown'].items()}

            print(f"Aggregation complete for {min_year_data}-{max_year_data}.")
            return render_template_string(
                RESULTS_HTML,
                title=f"Tax Report {min_year_data}-{max_year_data}",
                heading=f"Aggregated Tax Report ({min_year_data}-{max_year_data})",
                step=3,
                tax_year="all", # Pass 'all' to template for selection logic
                is_all_years_report=True,
                aggregated_summary=aggregated_summary,
                aggregated_stats=aggregated_stats,
                dispositions_in_year=[], # Empty for all years view
                rewards_in_year=[],     # Empty for all years view
                filename=filename,
                summary_stats=summary_stats_global,
                min_year=min_year_data,
                max_year=max_year_data,
                available_years_for_update=available_years_for_update,
                current_year_footer=datetime.datetime.now().year
            )

        else: # Single year report
            print(f"Calculating report for year: {tax_year}")
            tax_summary, year_stats, dispositions_in_year, rewards_in_year = calculate_report_for_year(all_taxable_events, tax_year)
            print(f"Calculation complete for {tax_year}.")
            return render_template_string(
                RESULTS_HTML,
                title=f"Tax Report {tax_year}",
                heading=f"Tax Report for {tax_year}",
                step=3,
                tax_year=tax_year, # Pass the specific year
                is_all_years_report=False,
                tax_summary=tax_summary,
                year_stats=year_stats,
                dispositions_in_year=dispositions_in_year,
                rewards_in_year=rewards_in_year,
                aggregated_summary={}, # Empty for single year view
                aggregated_stats={},   # Empty for single year view
                filename=filename,
                summary_stats=summary_stats_global,
                min_year=min_year_data,
                max_year=max_year_data,
                available_years_for_update=available_years_for_update,
                current_year_footer=datetime.datetime.now().year
            )

    except Exception as e:
        print(f"Error calculating report for {tax_year_display}: {traceback.format_exc()}")
        flash(f"Error generating report for {tax_year_display}: {e}", 'error')
        # Redirect back to select_year, as results failed
        return redirect(url_for('select_year'))

# --- Main Execution ---
if __name__ == '__main__':
    for dir_path in [app.config['UPLOAD_FOLDER'], app.config['SESSION_FILE_DIR']]:
         if not os.path.exists(dir_path):
             try: os.makedirs(dir_path); print(f"Created directory: {dir_path}")
             except OSError as e: print(f"FATAL: Could not create directory {dir_path}: {e}"); exit(1)
    # Set debug=False for production!
    app.run(debug=True, host='0.0.0.0', port=5000)

# --- END OF FILE crypto_tax_app_v2.py ---

# --- START OF FILE crypto_tax_app_v2.py ---

import os
import pandas as pd
from flask import Flask, request, render_template_string, redirect, url_for, flash, session
from flask_session import Session # *** Import Flask-Session ***
from werkzeug.utils import secure_filename
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation
import io
import traceback
import datetime
from collections import defaultdict
import time # Temporary for simulating processing time

# --- Configuration ---
UPLOAD_FOLDER = 'uploads_temp' # Temporary storage for uploads
ALLOWED_EXTENSIONS = {'csv'}
DECIMAL_PLACES = 8 # Precision for crypto amounts
CURRENCY_PLACES = 2 # Precision for CAD values

# Column Name Mappings (French to English) - Keep as is
FRENCH_TO_ENGLISH_MAP = {
    "Date": "Date", "Montant débité": "Amount Debited", "Actif débité": "Asset Debited",
    "Montant crédité": "Amount Credited", "Actif crédité": "Asset Credited", "Valeur du marché": "Market Value",
    "Devise de valeur du marché": "Market Value Currency", "Coût comptable": "Book Cost",
    "Devise du coût comptable": "Book Cost Currency", "Type": "Type", "Taux au comptant": "Spot Rate",
    "Taux d'achat/de vente": "Buy / Sell Rate", "Description": "Description"
}

# Transaction Type Mappings (French to English) - Keep as is
FRENCH_TO_ENGLISH_TYPES = {
    "Achat": "Buy", "Récompenses": "Reward", "Envoi": "Send", "Vente": "Sell",
    "Recevoir": "Receive", "Remise en bitcoins": "Reward", "Remises en Bitcoin": "Reward"
}

# --- Embedded CSS (Updated with New Design) ---
EMBEDDED_CSS = """
<style>
    /* Updated Quebec Crypto Tax Helper CSS */

    :root {
      --primary: #0047A0;        /* Quebec blue */
      --primary-dark: #003780;   /* Darker Quebec blue for hover */
      --primary-light: #3399FF;  /* Lighter blue for accents */
      --secondary: #22c55e;      /* Green for success/actions */
      --secondary-dark: #16a34a; /* Darker green for hover */
      --gray-100: #f3f4f6;       /* Lightest gray for backgrounds */
      --gray-200: #e5e7eb;       /* Light gray for borders/dividers */
      --gray-300: #d1d5db;       /* Medium gray for borders */
      --gray-600: #4b5563;       /* Dark gray for text/labels */
      --gray-800: #1f2937;       /* Darkest gray for headings */
      --success: #16a34a;        /* Darker green for text */
      --success-bg: #dcfce7;     /* Light green background */
      --danger: #dc2626;         /* Red for errors */
      --danger-bg: #fee2e2;      /* Light red background */
      --info: #2563eb;           /* Blue for info */
      --info-bg: #dbeafe;        /* Light blue background */
      --warning: #f59e0b;        /* Amber for warnings */
      --warning-bg: #fef3c7;     /* Light amber background */
      --card-shadow: 0 4px 12px -2px rgba(0, 71, 160, 0.15), 0 2px 6px -1px rgba(0, 71, 160, 0.1);
      --font-sans: 'Nunito', system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
      --gradient-main: linear-gradient(135deg, #2196F3 0%, #6C5CE7 100%); /* Adjusted slightly for a more vibrant feel */
      --gradient-button: linear-gradient(135deg, #0047A0 0%, #3399FF 100%);
    }

    /* --- Google Font Import --- */
    @import url('https://fonts.googleapis.com/css2?family=Nunito:wght@400;500;600;700&display=swap');

    /* --- General Body & Container --- */
    body {
      font-family: var(--font-sans);
      /* background: var(--gradient-main); */ /* Commented out gradient on body for better readability, applied elsewhere if needed */
      background-color: var(--gray-100); /* Use light gray as base background */
      background-attachment: fixed;
      line-height: 1.6;
      color: var(--gray-800);
      padding: 0;
      margin: 0;
      display: flex;
      flex-direction: column;
      min-height: 100vh;
    }

    .main-content {
      flex-grow: 1;
    }

    .container {
      max-width: 900px;
      margin: 40px auto;
      background-color: white;
      border-radius: 16px; /* Increased border radius */
      box-shadow: var(--card-shadow);
      padding: 32px;
      position: relative;
      overflow: hidden; /* Important for pseudo-element */
    }

    /* Add subtle Quebec flag pattern to container */
    /* Disabled by default as it can be distracting, uncomment if desired */
    /*
    .container::before {
      content: '';
      position: absolute;
      top: 0;
      right: 0;
      width: 80px;
      height: 80px;
      background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'%3E%3Crect width='100' height='100' fill='%230047A0' /%3E%3Cpath d='M50 15 L85 50 L50 85 L15 50 Z' fill='white' /%3E%3Cpath d='M30 30 Q35 40 30 50 Q25 40 30 30 Z M70 30 Q75 40 70 50 Q65 40 70 30 Z M30 50 Q35 60 30 70 Q25 60 30 50 Z M70 50 Q75 60 70 70 Q65 60 70 50 Z' fill='%230047A0' /%3E%3C/svg%3E");
      background-size: contain;
      opacity: 0.05;
      pointer-events: none;
      z-index: 0;
    }
    */
    /* --- Header --- */
    .app-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding-bottom: 20px;
      margin-bottom: 30px;
      border-bottom: 1px solid var(--gray-200);
      position: relative; /* Ensure header content is above pseudo-elements if they exist */
      z-index: 1;
    }

    .logo {
      display: flex;
      align-items: center;
      gap: 12px;
      text-decoration: none;
      position: relative;
    }

    .logo-icon {
      font-size: 1.8rem; /* Original Bitcoin icon size */
      color: var(--primary);
      /* Raccoon/Mask Icon - Uncomment below if you prefer the SVG icon */
      /*
      display: inline-block;
      background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 36 36' fill='%230047A0'%3E%3Cpath d='M18,12c-8,0-12,4-12,4s4,8,12,8s12-8,12-8S26,12,18,12z'/%3E%3Ccircle cx='18' cy='16' r='5' fill='white'/%3E%3Ccircle cx='18' cy='16' r='3' fill='%230047A0'/%3E%3Cpath d='M7,8c0,0,2,4,5,6C7,14,7,8,7,8z'/%3E%3Cpath d='M29,8c0,0-2,4-5,6C29,14,29,8,29,8z'/%3E%3C/svg%3E");
      width: 36px;
      height: 36px;
      vertical-align: middle;
      */
    }

    .logo-text {
      font-size: 1.3rem; /* Increased size */
      font-weight: 700;
      color: var(--gray-800);
      text-shadow: 0px 1px 1px rgba(0, 0, 0, 0.1);
    }

    .main-nav {
      display: flex;
      gap: 16px;
    }

    .nav-link {
      color: var(--gray-600);
      text-decoration: none;
      font-weight: 600; /* Bolder nav links */
      padding: 10px 14px; /* Slightly larger padding */
      border-radius: 8px;
      transition: all 0.2s ease;
    }

    .nav-link:hover, .nav-link.active {
      background-color: rgba(0, 71, 160, 0.1); /* Subtle hover background */
      color: var(--primary);
    }

    /* --- Footer --- */
    .app-footer {
      margin-top: auto;
      padding: 20px 0;
      /* background-color: rgba(255, 255, 255, 0.9); */ /* Using solid white for footer */
      background-color: white;
      border-top: 1px solid rgba(0, 71, 160, 0.1); /* Subtle border */
    }

    .footer-content {
      max-width: 900px;
      margin: 0 auto;
      padding: 0 32px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      font-size: 0.875rem;
      color: var(--gray-600);
      flex-wrap: wrap;
      gap: 10px;
    }

    .footer-links {
      display: flex;
      gap: 16px;
    }

    .footer-links a {
      color: var(--primary); /* Links match primary color */
      text-decoration: none;
      font-weight: 500;
    }

    .footer-links a:hover {
      color: var(--primary-dark);
      text-decoration: underline;
    }


    /* --- Headings --- */
    h1 {
      color: var(--primary);
      font-size: 1.8rem;
      font-weight: 700;
      margin: 0 0 20px 0;
      padding-bottom: 15px;
      border-bottom: 3px solid var(--primary);
      text-align: center;
      position: relative;
    }
    /* Bitcoin symbol below h1 heading */
    h1::after {
      content: '₿';
      position: absolute;
      bottom: -12px; /* Position below the border */
      left: 50%;
      transform: translateX(-50%);
      background: white; /* Match container background */
      padding: 0 12px;
      font-size: 1.5rem;
      color: var(--primary);
    }


    h2 {
      color: var(--primary-dark); /* Darker blue for H2 */
      font-size: 1.4rem;
      margin-top: 35px;
      margin-bottom: 15px;
      padding-bottom: 10px;
      border-bottom: 2px solid var(--gray-200);
    }

    h3 {
        color: var(--primary-dark);
        font-size: 1.1rem;
        margin-top: 20px;
        margin-bottom: 10px;
    }

    /* --- Alert/Flash Messages --- */
    .flash-message { /* Common base class */
      padding: 12px 16px;
      border-radius: 12px; /* Rounded corners */
      margin-bottom: 20px;
      border-left-width: 4px;
      border-left-style: solid;
      opacity: 1; /* Start visible for JS transition */
      box-shadow: 0 2px 5px rgba(0, 0, 0, 0.05); /* Subtle shadow */
    }

    .error {
      background-color: var(--danger-bg);
      color: var(--danger);
      border-left-color: var(--danger);
    }

    .success {
      background-color: var(--success-bg);
      color: var(--success);
      border-left-color: var(--success);
    }

    .info {
      background-color: var(--info-bg);
      color: var(--info);
      border-left-color: var(--info);
    }

    /* --- Form Styling --- */
    .form-group {
      margin-bottom: 24px;
    }

    label {
      display: block;
      margin-bottom: 10px; /* More space below label */
      font-weight: 600;
      color: var(--gray-600);
      font-size: 0.95rem; /* Slightly larger label */
    }

    input[type=file], input[type=number], select {
      display: block;
      box-sizing: border-box;
      width: 100%;
      padding: 12px 16px; /* Increased padding */
      font-size: 1rem;
      border: 1px solid var(--gray-300);
      border-radius: 12px; /* More rounded corners */
      background-color: white;
      transition: border-color 0.15s ease-in-out, box-shadow 0.15s ease-in-out;
      color: var(--gray-800);
    }
    /* Style file input button */
    input[type=file]::file-selector-button {
        background: var(--gradient-button); /* Gradient background */
        color: white;
        border: none;
        padding: 8px 14px; /* Adjusted padding */
        border-radius: 8px; /* Rounded corners */
        cursor: pointer;
        margin-right: 12px; /* Space after button */
        transition: opacity 0.15s ease-in-out;
        font-weight: 600;
    }
    input[type=file]::file-selector-button:hover {
        opacity: 0.9; /* Slight fade on hover */
    }


    input[type=file]:focus, input[type=number]:focus, select:focus {
      outline: none;
      border-color: var(--primary-light); /* Lighter blue focus border */
      box-shadow: 0 0 0 3px rgba(0, 71, 160, 0.2); /* Adjusted focus shadow */
    }

    /* --- Buttons --- */
    button, input[type=submit] {
      background: var(--gradient-button); /* Gradient background */
      color: white;
      border: none;
      border-radius: 12px; /* Rounded corners */
      padding: 14px 20px; /* Larger padding */
      font-size: 1rem;
      font-weight: 600;
      cursor: pointer;
      width: 100%;
      transition: all 0.15s ease-in-out;
      text-align: center;
      display: inline-block;
      box-shadow: 0 2px 5px rgba(0, 71, 160, 0.2); /* Base shadow */
    }

    button:hover, input[type=submit]:hover {
      box-shadow: 0 4px 10px rgba(0, 71, 160, 0.3); /* Enhanced hover shadow */
      transform: translateY(-1px); /* Slight lift on hover */
    }
    button:active, input[type=submit]:active {
      transform: translateY(1px); /* Push down on click */
      box-shadow: 0 1px 3px rgba(0, 71, 160, 0.2); /* Reduced shadow on click */
    }


    button:disabled, input[type=submit]:disabled {
        opacity: 0.6;
        cursor: not-allowed;
        transform: none; /* Disable transforms */
        box-shadow: none; /* Remove shadow */
    }

    .btn-secondary {
      background: linear-gradient(135deg, var(--secondary-dark) 0%, var(--secondary) 100%); /* Green gradient */
    }
    .btn-secondary:hover {
      box-shadow: 0 4px 10px rgba(22, 163, 74, 0.3); /* Green hover shadow */
    }


    .btn-link { /* Simple link styling */
        color: var(--primary);
        text-decoration: none;
        background: none;
        border: none;
        padding: 0;
        font: inherit;
        cursor: pointer;
    }
    .btn-link:hover {
        text-decoration: underline;
        color: var(--primary-dark);
    }

    /* --- Progress Stepper --- */
    .stepper {
      display: flex;
      margin-bottom: 40px;
      padding-bottom: 20px;
      border-bottom: 1px solid var(--gray-200);
      justify-content: space-around;
      list-style: none;
      padding-left: 0;
      counter-reset: step-counter;
    }

    .step {
      flex: 1;
      text-align: center;
      position: relative;
    }

    /* Line connector */
    .step:not(:last-child)::after {
      content: '';
      position: absolute;
      top: 15px; /* Position line vertically centered with number */
      left: 50%; /* Start line from center of step */
      width: 100%;
      height: 2px;
      background-color: var(--gray-300);
      z-index: 1; /* Behind the number */
      transform: translateX(calc(18px)); /* Adjusted offset slightly past larger number */
    }
    /* Line color for completed steps */
    .step.completed:not(:last-child)::after {
        background-color: var(--primary); /* Use primary blue for completed line */
    }
    /* Adjust last step's connector */
    .step:last-child::after {
        display: none; /* No line after the last step */
    }


    .step-number {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      width: 36px; /* Larger step number */
      height: 36px;
      border-radius: 50%;
      background-color: var(--gray-300);
      color: white;
      font-weight: 600;
      margin-bottom: 8px;
      position: relative; /* Ensure it's above the line */
      z-index: 2;
      border: 2px solid white; /* Add border to lift it visually */
      box-shadow: 0 1px 5px rgba(0,0,0,0.1); /* Subtle shadow */
    }

    .step.active .step-number {
      background: var(--gradient-button); /* Gradient for active step */
      border-color: rgba(255, 255, 255, 0.7); /* Slightly transparent border */
      box-shadow: 0 0 0 3px rgba(0, 71, 160, 0.2); /* Focus ring */
    }

    .step.completed .step-number {
      background-color: var(--primary); /* Primary blue for completed */
      border-color: rgba(255, 255, 255, 0.7);
    }
    /* Add checkmark for completed steps */
    .step.completed .step-number::before {
        content: '✔';
        font-size: 16px;
        color: white;
    }

    .step-label {
      display: block; /* Ensure label is block */
      font-size: 0.95rem; /* Slightly larger label */
      color: var(--gray-600);
    }

    .step.active .step-label {
      color: var(--primary);
      font-weight: 600;
    }
    .step.completed .step-label {
      color: var(--primary); /* Use primary blue for completed label too */
      font-weight: 500;
    }


    /* --- Card Components (Used in Results) --- */
    .card {
      background-color: white;
      border-radius: 12px; /* Consistent rounded corners */
      box-shadow: var(--card-shadow);
      margin-bottom: 28px; /* Increased spacing */
      overflow: hidden; /* Ensure content respects border radius */
      border: 1px solid var(--gray-200); /* Subtle border */
      transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .card:hover {
        transform: translateY(-2px); /* Lift effect on hover */
        box-shadow: 0 8px 16px -4px rgba(0, 71, 160, 0.15); /* Enhanced hover shadow */
    }


    .card-header {
      /* background-color: var(--gray-100); */
      background: linear-gradient(to right, var(--primary-light), var(--primary)); /* Gradient header */
      padding: 16px 20px;
      font-weight: 600;
      border-bottom: 1px solid var(--gray-200); /* Keep separator */
      color: white; /* White text on gradient */
    }

    .card-body {
      padding: 22px; /* Slightly more padding */
    }
    .card-footer {
      background-color: var(--gray-100);
      padding: 14px 20px;
      border-top: 1px solid var(--gray-200);
      font-size: 0.9rem;
      color: var(--gray-600);
    }

    /* --- Tax Form Summary Styling (Results Page) --- */
    .tax-summary { /* Use card styling */
      margin-bottom: 30px;
    }

    .tax-heading { /* Use card-header */
      font-size: 1.25rem; /* Adjusted size */
    }

    .tax-line {
      display: flex;
      justify-content: space-between;
      align-items: center; /* Align items vertically */
      padding: 14px 0; /* Increased padding */
      border-bottom: 1px dashed var(--gray-200); /* Lighter dash */
      flex-wrap: wrap; /* Allow wrapping on small screens */
    }

    .tax-line:last-child {
      border-bottom: none;
      padding-bottom: 0;
    }

    .tax-label {
      font-weight: 500;
      color: var(--gray-600);
      flex-basis: 65%; /* Allocate space */
      padding-right: 10px; /* Space between label and value */
    }

    .tax-value {
      font-family: "SFMono-Regular", Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace; /* Monospace font */
      font-size: 1.1rem;
      font-weight: 600;
      text-align: right;
      flex-basis: 35%; /* Allocate space */
      background: rgba(0,0,0,0.03); /* Subtle background for value */
      padding: 6px 12px;
      border-radius: 6px;
    }

    .tax-value.gain {
      color: var(--success);
      background: rgba(22, 163, 74, 0.05); /* Light green background for gain */
    }

    .tax-value.loss {
      color: var(--danger);
      background: rgba(220, 38, 38, 0.05); /* Light red background for loss */
    }

    .tax-note {
      margin-top: 18px; /* Increased margin */
      font-size: 0.9rem; /* Slightly larger note */
      color: var(--gray-600);
      background-color: var(--warning-bg); /* Warning background */
      padding: 14px 18px; /* More padding */
      border-radius: 10px; /* Rounded corners */
      border-left: 4px solid var(--warning); /* Warning border */
      position: relative; /* For potential future icon */
    }
    .tax-note strong {
        color: var(--warning); /* Make strong text use warning color */
    }


    /* --- Statistics Display (Results Page) --- */
    .stats-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); /* Adjust minmax */
      gap: 18px; /* Increased gap */
      margin-top: 12px; /* Reduced margin */
    }

    .stat-card { /* Simpler styling than full card */
      background-color: white; /* White background for stat cards */
      border-radius: 10px; /* Rounded corners */
      padding: 18px; /* Increased padding */
      border: 1px solid var(--gray-200);
      box-shadow: 0 2px 8px rgba(0,0,0,0.03); /* Lighter shadow */
      transition: transform 0.2s ease;
    }
    .stat-card:hover {
        transform: translateY(-3px); /* Lift on hover */
        box-shadow: 0 4px 12px rgba(0,0,0,0.08); /* Enhanced shadow */
    }


    .stat-name {
      color: var(--gray-600);
      font-size: 0.875rem;
      margin-bottom: 8px; /* Increased space */
      display: block; /* Ensure it takes full width */
      font-weight: 500;
    }

    .stat-value {
      font-size: 1.4rem; /* Adjusted size */
      font-weight: 700; /* Bolder value */
      color: var(--primary-dark); /* Use dark blue for default stat value */
      display: block; /* Ensure it takes full width */
      word-wrap: break-word; /* Prevent overflow */
    }

    /* Specific value coloring */
    .stat-value.positive {
      color: var(--success);
    }
    .stat-value.negative {
      color: var(--danger);
    }


    /* Reward Breakdown List */
    .reward-breakdown-list {
        list-style: none;
        padding-left: 0;
        margin-top: 18px; /* Space above list */
        background: var(--gray-100); /* Light background for list area */
        border-radius: 10px;
        padding: 12px; /* Padding around list items */
    }
    .reward-breakdown-item {
        display: flex;
        justify-content: space-between;
        font-size: 0.9rem;
        padding: 8px 12px; /* Padding for each item */
        border-bottom: 1px dashed var(--gray-200);
        border-radius: 6px; /* Rounded corners for items */
        transition: background-color 0.15s ease;
    }
    .reward-breakdown-item:hover {
        background-color: rgba(255, 255, 255, 0.7); /* Subtle hover highlight */
    }

    .reward-breakdown-item:last-child {
        border-bottom: none;
    }
    .reward-type {
        color: var(--gray-600);
        font-weight: 500;
    }
    .reward-details {
        font-weight: 600; /* Slightly bolder details */
        font-family: monospace;
        color: var(--primary-dark); /* Dark blue for reward value */
    }


    /* --- Collapsible Sections (Details) --- */
    details {
      margin-bottom: 18px; /* Increased space */
      border-radius: 12px; /* Rounded corners */
      overflow: hidden; /* Important for border-radius */
      border: 1px solid var(--gray-200);
      background-color: white; /* Background for content area */
      box-shadow: 0 2px 8px rgba(0,0,0,0.03); /* Subtle shadow */
    }

    details > summary {
      padding: 16px 20px 16px 44px; /* Adjusted padding for custom marker */
      /* background-color: var(--gray-100); */
      background: linear-gradient(to right, rgba(0, 71, 160, 0.02), rgba(0, 71, 160, 0.08)); /* Subtle blue gradient */
      cursor: pointer;
      font-weight: 600;
      color: var(--primary-dark);
      list-style: none; /* Remove default marker */
      position: relative;
      transition: background-color 0.2s ease;
      border-bottom: 1px solid var(--gray-200); /* Separator line */
    }
    details > summary::-webkit-details-marker { display: none; } /* Hide marker in Chrome/Safari */
    details > summary::before { /* Custom marker */
        content: '►';
        position: absolute;
        left: 20px;
        top: 50%;
        transform: translateY(-50%);
        font-size: 0.8em;
        transition: transform 0.2s ease;
        color: var(--primary);
    }


    details[open] > summary {
      /* background-color: var(--gray-200); */
      background: linear-gradient(to right, rgba(0, 71, 160, 0.08), rgba(0, 71, 160, 0.15)); /* Darker gradient when open */
      border-bottom-color: var(--gray-300); /* Darker border when open */
    }
    details[open] > summary::before {
        transform: translateY(-50%) rotate(90deg);
    }


    details > .details-content { /* Wrapper for content inside details */
      padding: 18px; /* Increased padding */
      border-top: 1px solid var(--gray-200); /* Line between summary and content */
    }
    details[open] > .details-content {
        animation: fadeIn 0.3s ease-in; /* Fade in content */
    }


    /* --- Table Improvements --- */
    .table-container { /* Optional: for horizontal scrolling on small screens */
        overflow-x: auto;
        -webkit-overflow-scrolling: touch; /* Smooth scrolling on iOS */
        border-radius: 8px; /* Rounded corners for the scroll container */
        box-shadow: inset 0 0 0 1px var(--gray-200); /* Inner border */
    }

    table {
      width: 100%;
      border-collapse: separate; /* Use separate for border-spacing */
      border-spacing: 0;
      margin: 0; /* Remove default margins */
      font-size: 0.9rem; /* Base table font size */
    }

    th {
      /* background-color: var(--gray-100); */
      background: linear-gradient(to bottom, var(--gray-100), var(--gray-200)); /* Subtle gradient header */
      font-weight: 600;
      text-align: left;
      padding: 14px 12px; /* Adjusted padding */
      border-bottom: 2px solid var(--primary-light); /* Use light blue border */
      color: var(--primary-dark); /* Header text color */
      white-space: nowrap; /* Prevent header text wrapping */
      position: sticky; /* Sticky header for scrolling tables */
      top: 0; /* Stick to top */
      z-index: 1; /* Ensure header is above rows */
    }

    td {
      padding: 12px; /* Adjusted padding */
      border-bottom: 1px solid var(--gray-200);
      vertical-align: middle; /* Align cell content vertically */
      font-family: "SFMono-Regular", Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace; /* Monospace for data */
      font-size: 0.85rem; /* Slightly smaller data font */
    }
    td.numeric { /* Align numeric data right */
        text-align: right;
        font-feature-settings: "tnum"; /* Tabular nums for alignment */
        letter-spacing: -0.5px; /* Tighten spacing slightly */
    }
    td.gain {
        color: var(--success);
        font-weight: 500;
    }
    td.loss {
        color: var(--danger);
        font-weight: 500;
    }


    tr:hover {
      background-color: rgba(0, 71, 160, 0.03); /* Very subtle blue hover */
    }

    tr:last-child td {
      border-bottom: none; /* Remove border from last row */
    }

    /* --- Loading States & Transitions --- */
    .loading {
      display: none; /* Hidden by default */
      text-align: center;
      padding: 24px 0; /* Increased padding */
      margin: 24px 0;
    }

    .loading.active {
      display: block; /* Shown when active class is added */
    }

    .spinner {
      display: inline-block;
      width: 38px; /* Larger spinner */
      height: 38px;
      border: 3px solid rgba(0, 71, 160, 0.2); /* Lighter base border */
      border-radius: 50%;
      border-top-color: var(--primary); /* Primary blue spinner color */
      animation: spin 0.8s linear infinite; /* Faster spin */
    }

    @keyframes spin {
      to { transform: rotate(360deg); }
    }

    /* Page/content transitions */
    .fade-in {
      animation: fadeIn 0.4s ease-in-out; /* Slightly longer fade */
    }

    @keyframes fadeIn {
      from { opacity: 0; transform: translateY(10px); } /* Add subtle slide up */
      to { opacity: 1; transform: translateY(0); }
    }

    /* Button loading state */
    .btn-loading {
      position: relative;
      color: transparent !important; /* Hide text reliably */
      pointer-events: none; /* Prevent clicking while loading */
    }

    .btn-loading::after {
      content: "";
      position: absolute;
      /* Center the spinner */
      left: calc(50% - 10px); /* Adjust based on spinner size */
      top: calc(50% - 10px); /* Adjust based on spinner size */
      width: 20px; /* Spinner size */
      height: 20px;
      border: 2px solid rgba(255, 255, 255, 0.5); /* Spinner track */
      border-radius: 50%;
      border-top-color: white; /* Spinner color */
      animation: spin 0.8s linear infinite;
    }

    /* --- Responsive Adjustments --- */
    @media (max-width: 768px) {
      .container {
        margin: 20px;
        padding: 24px; /* Adjusted padding */
        border-radius: 12px; /* Consistent radius */
      }

      h1 { font-size: 1.6rem; }
      h2 { font-size: 1.3rem; }

      .app-header {
          flex-direction: column;
          align-items: flex-start;
          gap: 15px;
      }
      .main-nav {
          width: 100%;
          justify-content: flex-start; /* Align nav links left */
      }

      .tax-line {
          flex-direction: column;
          align-items: flex-start;
          gap: 5px; /* Add gap between label and value */
      }
      .tax-label, .tax-value {
          flex-basis: auto; /* Reset basis */
          width: 100%; /* Take full width */
          text-align: left; /* Align value left */
      }
      .tax-value { font-size: 1rem; }

      .stats-grid {
          grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); /* Smaller min width */
      }
      .stat-value { font-size: 1.2rem; }

      .footer-content {
          flex-direction: column;
          align-items: center;
          gap: 15px;
          text-align: center;
      }

      .stepper {
          flex-direction: column;
          align-items: flex-start;
          gap: 15px;
          border-bottom: none;
      }
      .step {
          width: 100%;
          text-align: left;
      }
      .step::after { display: none; } /* Hide connector lines on mobile */
      .step-number { margin-bottom: 4px; }
      .step-label { font-size: 1rem; }
    }

    /* For very small screens */
    @media (max-width: 480px) {
      .container {
        margin: 10px;
        padding: 16px;
        border-radius: 8px; /* Smaller radius */
      }

      h1 { font-size: 1.4rem; }
      h2 { font-size: 1.1rem; }

      .form-group { margin-bottom: 16px; }
      button, input[type=submit] { padding: 10px 16px; font-size: 0.9rem; border-radius: 8px; }
      input[type=file], input[type=number], select { border-radius: 8px; }


      .logo-text { font-size: 1rem; }
      .nav-link { padding: 6px 8px; font-size: 0.9rem; }

      .footer-content, .footer-links a { font-size: 0.8rem; }

      /* Further reduce table font size if needed */
      table, td, th { font-size: 0.8rem; padding: 8px 6px; }
      td.numeric { font-size: 0.8rem; }

      .stat-value { font-size: 1.1rem; }
    }
</style>
"""

# --- Embedded JavaScript ---
EMBEDDED_JS = """
<script>
    // static/js/main.js

    document.addEventListener('DOMContentLoaded', function() {

      // --- Add loading state to forms ---
      const forms = document.querySelectorAll('form');
      forms.forEach(form => {
        form.addEventListener('submit', function(event) {
          // Find the submit button within *this* specific form
          const submitBtn = form.querySelector('input[type="submit"], button[type="submit"]');

          if (submitBtn && !submitBtn.classList.contains('btn-loading')) {
            submitBtn.classList.add('btn-loading');
            submitBtn.disabled = true;

            // Find a loading indicator *associated* with this form if possible
            // (e.g., placed right after the form or button)
            // This example assumes a single global one '.loading' for simplicity
            const loadingEl = document.querySelector('.loading');
            if (loadingEl) {
              loadingEl.classList.add('active');
            }
          }
          // Prevent double submission if already loading
          else if (submitBtn && submitBtn.classList.contains('btn-loading')) {
              console.log("Form already submitting...");
              event.preventDefault(); // Stop the second submission
          }
        });
      });

      // --- Auto-hide flash messages after 5 seconds ---
      const flashMessages = document.querySelectorAll('.flash-message'); // Target the base class
      flashMessages.forEach(message => {
        // Ensure message is initially visible before starting timeout
        message.style.opacity = '1';
        message.style.display = 'block'; // Or flex, grid etc. depending on layout

        setTimeout(() => {
          message.style.transition = 'opacity 0.5s ease-out, transform 0.5s ease-out'; // Add transform transition
          message.style.opacity = '0';
          message.style.transform = 'translateY(-10px)'; // Add subtle slide up effect

          // Remove from DOM after transition completes
          setTimeout(() => {
               if (message.parentNode) { // Check if it still exists
                   message.parentNode.removeChild(message);
               }
          }, 500); // Matches transition duration
        }, 5000); // 5 seconds delay
      });

      // --- Enhanced details elements ---
      const detailsElements = document.querySelectorAll('details');
      detailsElements.forEach(details => {
        const summary = details.querySelector('summary');
        //const content = details.querySelector('.details-content'); // Assuming content is wrapped

        // Optional: Smooth open/close animation (can be complex)
        // Basic toggle listener for scrolling
        details.addEventListener('toggle', function(event) {
          if (this.open) {
            // Scroll the summary into view smoothly
             // Add a small delay to allow the element to fully render open before scrolling
            setTimeout(() => {
                summary.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
            }, 100);
          }
        });
      });

      // --- Activate current navigation link (using Flask endpoint) ---
      const navLinks = document.querySelectorAll('.main-nav .nav-link');
      const currentEndpoint = "{{ request.endpoint }}"; // Get endpoint from Flask context

      navLinks.forEach(link => {
          const linkHref = link.getAttribute('href');
          let linkEndpoint = null;

          // Try to match href to known endpoints (adjust as needed)
          if (linkHref === "{{ url_for('index') }}") {
              linkEndpoint = 'index';
          } else if (linkHref === "#disclaimer-footer") {
              // Disclaimer is not a separate page/endpoint, so ignore for active state
              linkEndpoint = null;
          }
          // *** THE PROBLEMATIC LINES HAVE BEEN REMOVED FROM HERE ***

          if (linkEndpoint && linkEndpoint === currentEndpoint) {
              link.classList.add('active');
          } else {
              link.classList.remove('active'); // Ensure others are not active
          }
      });

    }); // End DOMContentLoaded
</script>
"""


# --- HTML TEMPLATES (Updated with new structure and CSS classes) ---

# Base structure common to all templates
HTML_BASE_START = f"""
<!doctype html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
    <title>{{{{ title }}}} - Quebec Crypto Tax Helper</title>
    {EMBEDDED_CSS}
    <link rel="icon" href="data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22><text y=%22.9em%22 font-size=%2290%22>₿</text></svg>">
</head>
<body>
    <div class="main-content"> <!-- Added for footer positioning -->
        <header class="app-header container"> <!-- Header inside container -->
            <a href="{{{{ url_for('index') }}}}" class="logo">
                <span class="logo-icon">₿</span>
                <span class="logo-text">Quebec Crypto Tax Helper</span>
            </a>
            <nav class="main-nav">
                <a href="{{{{ url_for('index') }}}}" class="nav-link {{{{'active' if request.endpoint == 'index' else ''}}}}">Home</a>
                <!-- Add more nav links if needed -->
                 <a href="#disclaimer-footer" class="nav-link">Disclaimer</a>
            </nav>
        </header>

        <div class="container fade-in"> <!-- Main content area -->
            <!-- Stepper -->
            <ol class="stepper">
                <li class="step {{{{'active' if step == 1 else ('completed' if step > 1 else '')}}}}">
                    <span class="step-number"></span>
                    <span class="step-label">1. Upload History</span>
                </li>
                <li class="step {{{{'active' if step == 2 else ('completed' if step > 2 else '')}}}}">
                    <span class="step-number"></span>
                    <span class="step-label">2. Select Year</span>
                </li>
                <li class="step {{{{'active' if step == 3 else ''}}}}">
                    <span class="step-number"></span>
                    <span class="step-label">3. View Report</span>
                </li>
            </ol>

            <h1>{{{{ heading }}}}</h1>

            <!-- Flash messages -->
            {{% with messages = get_flashed_messages(with_categories=true) %}}
              {{% if messages %}}
                {{% for category, message in messages %}}
                  <div class="flash-message {{{{ category }}}}">{{{{ message }}}}</div>
                {{% endfor %}}
              {{% endif %}}
            {{% endwith %}}

            <!-- Loading Indicator -->
            <div class="loading"><div class="spinner"></div></div>

            <!-- Page specific content goes here -->
"""

HTML_BASE_END = f"""
            <!-- End Page specific content -->
        </div> <!-- End container -->
    </div> <!-- End main-content -->

    <footer class="app-footer">
      <div class="footer-content">
        <p>© {{{{ current_year_footer }}}} Quebec Crypto Tax Helper</p>
        <div class="footer-links">
          <!-- <a href="#about">About</a> -->
          <!-- <a href="#privacy">Privacy</a> -->
          <a href="#disclaimer-footer">Disclaimer</a>
        </div>
      </div>
      <div class="container" style="padding-top: 10px; padding-bottom: 10px; margin-top:10px; font-size: 0.8rem; color: var(--gray-600); border-radius: 10px; background-color: var(--warning-bg); border-left: 4px solid var(--warning);" id="disclaimer-footer">
          <p><strong>Disclaimer:</strong> This tool is for informational and educational purposes only and provides a simplified calculation based on publicly available information regarding Quebec and Canadian tax rules for cryptocurrency as of late 2024. It requires a *complete* transaction history for potentially accurate Adjusted Cost Base (ACB) calculations. Tax laws are complex and subject to change. This tool does not constitute financial or tax advice. Calculations may not cover all transaction types or specific tax situations (e.g., superficial losses, specific business income rules). **Always consult a qualified Quebec tax professional** for advice tailored to your individual circumstances before making any tax filing decisions. Use of this tool is at your own risk.</p>
      </div>
    </footer>

    {EMBEDDED_JS}
</body>
</html>
"""

# --- Specific Page Templates ---

INDEX_HTML = HTML_BASE_START + """
            <p style="text-align: center; color: var(--gray-600); margin-bottom: 30px;">
                Upload your <strong>complete</strong> transaction history CSV file (English or French format from supported platforms like Shakepay). The tool will process the entire history to calculate accurate cost bases for tax reporting.
            </p>

            <form method="post" enctype="multipart/form-data" action="{{ url_for('upload_file') }}">
                <div class="form-group">
                    <label for="file">Select Full Transaction History CSV File:</label>
                    <input type="file" name="file" id="file" required accept=".csv">
                </div>
                <button type="submit">Upload and Process History</button>
            </form>
""" + HTML_BASE_END


SELECT_YEAR_HTML = HTML_BASE_START + """
            <div class="info flash-message"> <!-- Using flash-message style for consistency -->
                <p>Successfully processed transaction history from file: <strong>{{ filename }}</strong></p>
                <p style="font-size: 0.9em; margin-top: 5px;">Detected transaction year range: {{ min_year }} - {{ max_year }}</p>
            </div>

            <p style="text-align: center; color: var(--gray-600); margin-bottom: 30px;">
                Now, please select the specific tax year for which you want to generate the report.
            </p>

            <form method="post" action="{{ url_for('show_results') }}">
                 <div class="form-group">
                    <label for="tax_year">Select Tax Year or Option:</label>
                    <select name="tax_year" id="tax_year" required>
                        <option value="all" {{ 'selected' if default_year == 'all' else '' }}>All Years (Summary)</option>
                        {% for year in available_years %}
                            {% if year != 'all' %} {# Ensure 'all' isn't duplicated if passed in list #}
                            <option value="{{ year }}" {{ 'selected' if year == default_year else '' }}>{{ year }}</option>
                            {% endif %}
                        {% endfor %}
                    </select>
                </div>
                <button type="submit" class="btn-secondary">Generate Report</button>
            </form>

            <p style="margin-top: 30px; text-align: center;">
                <a href="{{ url_for('index') }}" class="btn-link">Upload a different file</a>
            </p>
""" + HTML_BASE_END


RESULTS_HTML = HTML_BASE_START + """
            <div class="info flash-message" style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px;">
                 <span>Report for Tax Year: <strong>{{ tax_year }}</strong></span>
                 <span>File: <strong>{{ filename }}</strong> ({{ summary_stats['total_transactions'] }} transactions processed)</span>
            </div>

            <!-- Update Year Form -->
            <form method="post" action="{{ url_for('show_results') }}" style="margin-bottom: 30px; display: flex; align-items: flex-end; gap: 15px; flex-wrap: wrap; background-color: var(--gray-100); padding: 15px; border-radius: 12px;">
                 <div class="form-group" style="margin-bottom: 0; flex-grow: 1;">
                     <label for="tax_year_select" style="margin-bottom: 5px;">View Report For:</label>
                     <select name="tax_year" id="tax_year_select" required style="width: auto; display: inline-block; padding: 8px 10px; min-width: 150px;">
                         <option value="all" {{ 'selected' if tax_year == 'all' else '' }}>All Years (Summary)</option>
                         {% for year in available_years_for_update %} {# Use a distinct variable name if needed #}
                             {% if year != 'all' %}
                             <option value="{{ year }}" {{ 'selected' if year|string == tax_year|string else '' }}>{{ year }}</option>
                             {% endif %}
                         {% endfor %}
                     </select>
                 </div>
                 <button type="submit" style="width: auto; padding: 9px 18px; margin-bottom: 0; flex-shrink: 0;">Update Report</button>
                 <a href="{{ url_for('index') }}" class="btn-link" style="margin-bottom: 5px;">Upload New File</a>
            </form>

            <!-- Tax Form Summary Card -->
            {% if not is_all_years_report %} {# Only show TP form summary for single year reports #}
            <div class="card tax-summary">
                <div class="card-header tax-heading">TP-21.4.39-V Summary for {{ tax_year }}</div>
                <div class="card-body">
                    <div class="tax-line">
                         <span class="tax-label">Part 4.1 - Line 65: Capital gains/(losses) <strong>before June 25, {{ tax_year + 1 }}</strong>:</span>
                         <span class="tax-value {{ 'loss' if tax_summary['before_cutoff'] < 0 else 'gain' }}">{{ tax_summary['before_cutoff'] | currency }}</span>
                    </div>
                     <div class="tax-line">
                         <span class="tax-label">Part 4.2 - Line 98: Capital gains/(losses) <strong>on or after June 25, {{ tax_year + 1 }}</strong>:</span>
                         <span class="tax-value {{ 'loss' if tax_summary['after_cutoff'] < 0 else 'gain' }}">{{ tax_summary['after_cutoff'] | currency }}</span>
                    </div>
                    <div class="tax-line">
                         <span class="tax-label">Part 6.2 - Line 135: Interest income (Rewards/Cashback):</span>
                         <span class="tax-value gain">{{ tax_summary['reward_income'] | currency }}</span>
                    </div>
                    <p class="tax-note">
                        <strong>Important:</strong> Enter these calculated amounts on the corresponding lines of form TP-21.4.39-V for tax year <strong>{{ tax_year }}</strong>. Follow form instructions for subsequent calculations. Consult a tax professional to confirm.
                    </p>
                </div>
            </div>
            {% else %} {# Show aggregated summary for "All Years" report #}
            <div class="card tax-summary">
                <div class="card-header tax-heading">Aggregated Summary for {{ min_year }} - {{ max_year }}</div>
                <div class="card-body">
                    <div class="tax-line">
                         <span class="tax-label">Total Capital Gains/(Losses) ({{ min_year }}-{{ max_year }}):</span>
                         <span class="tax-value {{ 'loss' if aggregated_summary['total_gain_loss'] < 0 else 'gain' }}">{{ aggregated_summary['total_gain_loss'] | currency }}</span>
                    </div>
                    <div class="tax-line">
                         <span class="tax-label">Total Reward Income ({{ min_year }}-{{ max_year }}):</span>
                         <span class="tax-value gain">{{ aggregated_summary['total_reward_income'] | currency }}</span>
                    </div>
                    <p class="tax-note">
                        <strong>Note:</strong> This is an aggregated summary across all years. Specific form lines apply only to individual tax years. Consult a tax professional for filing.
                    </p>
                </div>
            </div>
            {% endif %}

            <!-- Statistics Card -->
            <div class="card">
                <div class="card-header">Statistics for {{ 'Tax Year ' + tax_year|string if not is_all_years_report else 'All Years (' + min_year|string + '-' + max_year|string + ')' }}</div>
                <div class="card-body">
                    {% set stats = year_stats if not is_all_years_report else aggregated_stats %}
                    <div class="stats-grid">
                        <div class="stat-card">
                            <span class="stat-name">Total Dispositions</span>
                            <span class="stat-value">{{ stats['disposition_count'] }}</span>
                        </div>
                        <div class="stat-card">
                            <span class="stat-name">Total Proceeds:</span>
                            <span class="stat-value">{{ stats['total_proceeds'] | currency }}</span>
                        </div>
                        <div class="stat-card">
                            <span class="stat-name">Total Cost Base:</span>
                            <span class="stat-value">{{ stats['total_cost_disposed'] | currency }}</span>
                        </div>
                         {% if not is_all_years_report %} {# Avg Gain/Loss only for single year #}
                         <div class="stat-card">
                            <span class="stat-name">Average Gain/Loss:</span>
                            <span class="stat-value {{ 'negative' if stats['avg_gain_loss'] < 0 else 'positive' }}">{{ stats['avg_gain_loss'] | currency }}</span>
                         </div>
                         {% else %} {# Show Total Gain/Loss for all years #}
                         <div class="stat-card">
                            <span class="stat-name">Total Gain/Loss (CAD)</span>
                            {# Note: Aggregated Gain/Loss still uses old format as it's handled in the Aggregated Summary card #}
                            <span class="stat-value {{ 'negative' if aggregated_summary['total_gain_loss'] < 0 else 'positive' }}">{{ "%.2f"|format(aggregated_summary['total_gain_loss']) }}</span>
                         </div>
                         {% endif %}
                        <div class="stat-card">
                            <span class="stat-name">Largest Gain:</span>
                            <span class="stat-value positive">{{ stats['largest_gain'] | currency }}</span>
                        </div>
                        <div class="stat-card">
                            <span class="stat-name">Largest Loss:</span>
                            <span class="stat-value negative">{{ stats['largest_loss'] | currency }}</span>
                        </div>
                         <div class="stat-card">
                            <span class="stat-name">Reward Transactions:</span>
                            <span class="stat-value">{{ stats['reward_count'] }}</span>
                        </div>
                         <div class="stat-card">
                            <span class="stat-name">Total Reward Income:</span>
                            {# Use appropriate variable based on report type #}
                            <span class="stat-value positive">{{ (aggregated_summary['total_reward_income'] if is_all_years_report else tax_summary['reward_income']) | currency }}</span>
                        </div>
                    </div>
                    <!-- Reward Breakdown -->
                    {% if stats['reward_breakdown'] %}
                        <h3 style="margin-top: 25px;">Reward Breakdown:</h3>
                        <ul class="reward-breakdown-list">
                        {% for type, data in stats['reward_breakdown'].items()|sort %}
                            <li class="reward-breakdown-item">
                                <span class="reward-type">{{ type }}:</span>
                                <span class="reward-details">{{ data['count'] }} transactions, {{ data['value'] | currency }}</span>
                            </li>
                        {% endfor %}
                        </ul>
                    {% endif %}
                </div>
            </div>

            <!-- Detailed Transactions (Only show for single year reports) -->
            {% if not is_all_years_report %}
            <h2>Transaction Details for {{ tax_year }}</h2>
            <details>
                <summary>Dispositions: {{ year_stats['disposition_count'] }}</summary>
                <div class="details-content">
                    {% if dispositions_in_year %}
                    <div class="table-container">
                    <table>
                        <thead>
                            <tr>
                                <th>Date</th>
                                <th>Asset</th>
                                <th style="text-align: right;">Amount</th>
                                <th style="text-align: right;">Proceeds (CAD)</th>
                                <th style="text-align: right;">Cost Base (CAD)</th>
                                <th style="text-align: right;">Gain/(Loss) (CAD)</th>
                                <th>Period</th>
                             </tr>
                        </thead>
                        <tbody>
                            {% for tx in dispositions_in_year %}
                            <tr>
                                <td>{{ tx.date.strftime('%Y-%m-%d %H:%M') if tx.date else 'N/A' }}</td>
                                <td>{{ tx.asset }}</td>
                                <td class="numeric">{{ "%.8f"|format(tx.amount) }}</td>
                                <td class="numeric">{{ "%.2f"|format(tx.proceeds) }}</td>
                                <td class="numeric">{{ "%.2f"|format(tx.cost_base) }}</td>
                                <td class="numeric {{ 'loss' if tx.gain_loss < 0 else 'gain' }}">{{ "%.2f"|format(tx.gain_loss) }}</td>
                                <td>{{ tx.period.replace('_cutoff', '')|capitalize if tx.period else 'N/A' }}</td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                    </div>
                    {% else %}
                    <p>No disposition transactions found for this year.</p>
                    {% endif %}
                </div>
            </details>

            <details>
                <summary>Rewards: {{ year_stats['reward_count'] }}</summary>
                 <div class="details-content">
                     {% if rewards_in_year %}
                     <div class="table-container">
                     <table>
                        <thead>
                            <tr>
                                <th>Date</th>
                                <th>Asset</th>
                                <th style="text-align: right;">Amount</th>
                                <th style="text-align: right;">Income (CAD)</th>
                                <th>Description</th>
                             </tr>
                        </thead>
                        <tbody>
                            {% for tx in rewards_in_year %}
                            <tr>
                                <td>{{ tx.date.strftime('%Y-%m-%d %H:%M') if tx.date else 'N/A' }}</td>
                                <td>{{ tx.asset }}</td>
                                <td class="numeric">{{ "%.8f"|format(tx.amount) }}</td>
                                <td class="numeric gain">{{ "%.2f"|format(tx.income) }}</td>
                                <td>{{ tx.description }}</td>
                            </tr>
                            {% endfor %}
                        </tbody>
                     </table>
                     </div>
                     {% else %}
                     <p>No reward transactions found for this year.</p>
                     {% endif %}
                 </div>
            </details>
            {% else %}
            <h2>Transaction Details</h2>
            <p class="info flash-message">Detailed transaction lists are not shown in the 'All Years' summary view. Please select an individual year to see detailed transactions.</p>
            {% endif %}
""" + HTML_BASE_END


# --- Flask App Setup (Identical Backend Logic) ---
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'default-non-secret-key-change-me') # Important: We will set this securely later
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_USE_SIGNER'] = True
app.config['SESSION_FILE_DIR'] = './.flask_session/'
Session(app)

# Create directories if they don't exist
if not os.path.exists(app.config['SESSION_FILE_DIR']):
    try:
        os.makedirs(app.config['SESSION_FILE_DIR'])
    except OSError as e:
        print(f"Error creating session directory: {e}")

if not os.path.exists(app.config['UPLOAD_FOLDER']):
    try:
        os.makedirs(app.config['UPLOAD_FOLDER'])
    except OSError as e:
        print(f"Error creating upload directory: {e}")

# --- Helper Functions (Identical) ---
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def quantize_decimal(value, places=DECIMAL_PLACES):
    if value is None: return Decimal(0)
    if not isinstance(value, Decimal):
        try: value = Decimal(str(value))
        except (TypeError, ValueError, InvalidOperation): return Decimal(0)
    rounding_precision = Decimal('1e-' + str(places))
    return value.quantize(rounding_precision, rounding=ROUND_HALF_UP)

def parse_decimal_french(value_str):
    if isinstance(value_str, (int, float, Decimal)): return Decimal(value_str)
    if not isinstance(value_str, str): return Decimal(0)
    cleaned_value = value_str.strip().replace(',', '.')
    if not cleaned_value: return Decimal(0)
    try: return Decimal(cleaned_value)
    except InvalidOperation: return Decimal(0)

# --- Custom Jinja Filter for Currency Formatting ---
def format_currency(value):
    try:
        # Ensure value is a Decimal
        if not isinstance(value, Decimal):
            value = Decimal(str(value))

        # Quantize to 2 decimal places
        value = quantize_decimal(value, CURRENCY_PLACES)

        # Determine sign and format
        prefix = '–$ ' if value < 0 else '$ '
        formatted_value = "{:,.2f}".format(abs(value)) # Comma separator, 2 decimals

        return prefix + formatted_value
    except (TypeError, ValueError, InvalidOperation):
        return "$ 0.00" # Default fallback

# Register the custom filter
@app.template_filter('currency')
def currency_filter(value):
    return format_currency(value)

# --- Core Processing Logic (Identical) ---
def process_full_history(filepath):
    all_taxable_events = []
    total_processed_rows = 0
    min_year = None
    max_year = None
    try:
        with open(filepath, 'r', encoding='utf-8-sig') as f:
            header_line = f.readline().strip()
            is_french = '"Montant crédité"' in header_line or '"Actif crédité"' in header_line or 'Montant crédité' in header_line
        df = pd.read_csv(filepath, dtype=str, keep_default_na=False, encoding='utf-8-sig')
        total_processed_rows = len(df)
        if is_french:
            print("French format detected.")
            missing_french_cols = [fr_col for fr_col in FRENCH_TO_ENGLISH_MAP.keys() if fr_col not in df.columns]
            essential_french = ["Date", "Type", "Montant débité", "Actif débité", "Montant crédité", "Actif crédité", "Valeur du marché"]
            truly_missing = [col for col in essential_french if col in missing_french_cols]
            if truly_missing: raise ValueError(f"Essential CSV columns missing (French): {', '.join(truly_missing)}")
            elif missing_french_cols: print(f"Warning: Optional French columns missing: {', '.join(missing_french_cols)}")
            df.rename(columns=FRENCH_TO_ENGLISH_MAP, inplace=True)
            if 'Type' in df.columns: df['Type'] = df['Type'].replace(FRENCH_TO_ENGLISH_TYPES)
            elif 'Type' not in df.columns: raise ValueError("Essential 'Type' column not found after attempting French mapping.")
        else: print("Assuming English format.")
        expected_columns = ['Date', 'Type', 'Amount Debited', 'Asset Debited', 'Amount Credited', 'Asset Credited', 'Market Value']
        missing_cols = [col for col in expected_columns if col not in df.columns]
        if missing_cols: raise ValueError(f"Essential CSV columns missing: {', '.join(missing_cols)}")
        if 'Book Cost' not in df.columns: df['Book Cost'] = '0'
        if 'Description' not in df.columns: df['Description'] = ''
        try: df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        except Exception as e: raise ValueError(f"Error parsing 'Date' column: {e}.")
        if df['Date'].isnull().all(): raise ValueError("No valid dates found in the 'Date' column.")
        num_bad_dates = df['Date'].isnull().sum()
        if num_bad_dates > 0: print(f"Warning: {num_bad_dates} row(s) had invalid dates and were skipped."); df.dropna(subset=['Date'], inplace=True)
        if df.empty: raise ValueError("CSV contains no valid transactions after handling invalid dates.")
        min_year = df['Date'].min().year
        max_year = df['Date'].max().year
        print(f"Detected transaction year range: {min_year} - {max_year}")
        financial_cols = ['Amount Debited', 'Amount Credited', 'Market Value', 'Book Cost']
        for col in financial_cols:
            try: df[col] = df[col].apply(parse_decimal_french)
            except Exception as e: raise ValueError(f"Unexpected error converting column '{col}' to Decimal: {e}")
        df['Asset Debited'] = df['Asset Debited'].fillna('').str.strip().str.upper()
        df['Asset Credited'] = df['Asset Credited'].fillna('').str.strip().str.upper()
        df['Description'] = df['Description'].fillna('')
        df.sort_values(by='Date', inplace=True)
        acb_data = {}
        cutoff_date = pd.Timestamp('2024-06-25 00:00:00')
        for index, row in df.iterrows():
            date=row['Date']; tx_type=row['Type']; asset_debited=row['Asset Debited']; amount_debited=quantize_decimal(row['Amount Debited'],DECIMAL_PLACES); asset_credited=row['Asset Credited']; amount_credited=quantize_decimal(row['Amount Credited'],DECIMAL_PLACES); market_value=quantize_decimal(row['Market Value'],CURRENCY_PLACES); book_cost=quantize_decimal(row['Book Cost'],CURRENCY_PLACES); description=row['Description']
            if tx_type in ['Buy','Reward','Receive'] and amount_credited > 0 and asset_credited:
                asset=asset_credited; amount=amount_credited
                value_at_receipt = market_value if market_value > 0 else book_cost
                if value_at_receipt <= 0:
                    if tx_type == 'Reward': print(f"Warning ({date}): Reward of {amount} {asset} has zero value. Assuming zero cost/income.")
                    else: print(f"Warning ({date}): Acquisition of {amount} {asset} has zero value. Assuming zero cost.")
                    value_at_receipt=Decimal(0)
                cost_for_acb=value_at_receipt
                if asset not in acb_data: acb_data[asset]={'quantity':Decimal(0),'total_cost':Decimal(0)}
                acb_data[asset]['quantity']+=amount; acb_data[asset]['total_cost']+=cost_for_acb
                if tx_type=='Reward': all_taxable_events.append({'date':date,'type':'reward','asset':asset,'amount':amount,'income':value_at_receipt,'description':description})
            elif (tx_type=='Sell' or (tx_type=='Send' and market_value > 0)) and amount_debited > 0 and asset_debited:
                asset=asset_debited; amount_disposed=amount_debited; proceeds=market_value
                if asset and amount_disposed > 0:
                    if asset not in acb_data or acb_data[asset]['quantity']<=Decimal('1e-12'): print(f"Warning ({date}): Disposition of {amount_disposed} {asset} but no prior ACB. Skipping."); continue
                    current_quantity=acb_data[asset]['quantity']; current_total_cost=acb_data[asset]['total_cost']
                    if amount_disposed > current_quantity+Decimal('1e-12'): print(f"Warning ({date}): Disposing {amount_disposed} {asset}, only {current_quantity} available. Adjusting."); amount_disposed=current_quantity
                    if current_quantity<=Decimal('1e-12'): print(f"Warning ({date}): Quantity of {asset} is zero. Skipping disposition."); continue
                    acb_per_unit=(current_total_cost/current_quantity) if current_quantity > 0 else Decimal(0)
                    cost_of_disposed=quantize_decimal(amount_disposed*acb_per_unit,CURRENCY_PLACES)
                    gain_loss=quantize_decimal(proceeds-cost_of_disposed,CURRENCY_PLACES)
                    period_flag='after_cutoff' if date >= cutoff_date else 'before_cutoff'
                    all_taxable_events.append({'date':date,'type':'disposition','asset':asset,'amount':amount_disposed,'proceeds':proceeds,'cost_base':cost_of_disposed,'gain_loss':gain_loss,'period':period_flag})
                    acb_data[asset]['quantity']-=amount_disposed; acb_data[asset]['total_cost']-=(amount_disposed*acb_per_unit)
                    if acb_data[asset]['quantity']<Decimal('1e-10'): acb_data[asset]['quantity']=Decimal(0); acb_data[asset]['total_cost']=Decimal(0)
                    elif acb_data[asset]['total_cost']<0: print(f"Warning ({date}): ACB cost for {asset} negative ({acb_data[asset]['total_cost']}), resetting to zero."); acb_data[asset]['total_cost']=Decimal(0)
        summary_stats={'total_transactions':total_processed_rows}
        return all_taxable_events, summary_stats, min_year, max_year
    except ValueError as ve: print(f"Data validation error: {ve}"); raise
    except FileNotFoundError: print(f"Error: Input file not found at {filepath}"); raise ValueError(f"Could not find the uploaded file.")
    except pd.errors.EmptyDataError: print("Error: CSV file is empty."); raise ValueError("Uploaded CSV is empty.")
    except Exception as e: print(f"Unexpected error in processing: {traceback.format_exc()}"); raise ValueError(f"Unexpected error during processing: {e}")

def calculate_report_for_year(all_taxable_events, tax_year):
    gains_losses = {'before_cutoff': Decimal(0), 'after_cutoff': Decimal(0)}; total_reward_income = Decimal(0)
    dispositions_in_year = []; rewards_in_year = []
    reward_stats = defaultdict(lambda: {'count': 0, 'value': Decimal(0)})
    disposition_count = 0; reward_count = 0; total_proceeds = Decimal(0); total_cost_disposed = Decimal(0)
    largest_gain = Decimal('-Infinity'); largest_loss = Decimal('Infinity'); assets_involved = set()
    for event in all_taxable_events:
        event_date = event.get('date')
        if not isinstance(event_date, pd.Timestamp): print(f"Skipping event due to invalid date type: {event}"); continue
        if event_date.year == tax_year:
            event_type = event.get('type')
            if event_type == 'disposition':
                disposition_count += 1; dispositions_in_year.append(event); assets_involved.add(event.get('asset','UNKNOWN'))
                proceeds=event.get('proceeds',Decimal(0)); cost_base=event.get('cost_base',Decimal(0)); gain_loss=event.get('gain_loss',Decimal(0)); period=event.get('period','unknown')
                total_proceeds+=proceeds; total_cost_disposed+=cost_base
                if period == 'before_cutoff': gains_losses['before_cutoff'] += gain_loss
                elif period == 'after_cutoff': gains_losses['after_cutoff'] += gain_loss
                else: print(f"Warning: Disposition on {event_date} has unknown period '{period}'. Assigning to after_cutoff."); gains_losses['after_cutoff']+=gain_loss
                if gain_loss > largest_gain: largest_gain = gain_loss
                if gain_loss < largest_loss: largest_loss = gain_loss
            elif event_type == 'reward':
                reward_count += 1; rewards_in_year.append(event); income = event.get('income', Decimal(0)); total_reward_income += income
                desc=event.get('description','Other Reward').lower(); category='Other Reward'
                if 'shakingsats' in desc: category='ShakingSats'
                elif 'cashback' in desc or 'remise' in desc: category='Cashback/Rebate'
                elif 'secretsats' in desc: category = 'SecretSats'
                reward_stats[category]['count'] += 1; reward_stats[category]['value'] += income
    avg_gain_loss = (gains_losses['before_cutoff'] + gains_losses['after_cutoff']) / disposition_count if disposition_count > 0 else Decimal(0)
    if largest_gain == Decimal('-Infinity'): largest_gain = Decimal(0)
    if largest_loss == Decimal('Infinity'): largest_loss = Decimal(0)
    tax_summary = {'before_cutoff': quantize_decimal(gains_losses['before_cutoff'], CURRENCY_PLACES), 'after_cutoff': quantize_decimal(gains_losses['after_cutoff'], CURRENCY_PLACES), 'reward_income': quantize_decimal(total_reward_income, CURRENCY_PLACES)}
    year_stats = {'disposition_count': disposition_count, 'reward_count': reward_count, 'total_proceeds': quantize_decimal(total_proceeds, CURRENCY_PLACES), 'total_cost_disposed': quantize_decimal(total_cost_disposed, CURRENCY_PLACES), 'avg_gain_loss': quantize_decimal(avg_gain_loss, CURRENCY_PLACES), 'largest_gain': quantize_decimal(largest_gain, CURRENCY_PLACES), 'largest_loss': quantize_decimal(largest_loss, CURRENCY_PLACES), 'reward_breakdown': {k: {'count': v['count'], 'value': quantize_decimal(v['value'], CURRENCY_PLACES)} for k, v in reward_stats.items()}, 'assets_involved': sorted(list(assets_involved))}
    dispositions_in_year.sort(key=lambda x: x.get('date', pd.Timestamp.min)); rewards_in_year.sort(key=lambda x: x.get('date', pd.Timestamp.min))
    return tax_summary, year_stats, dispositions_in_year, rewards_in_year


# --- Flask Routes ---
@app.route('/', methods=['GET'])
def index():
    session.pop('all_taxable_events', None); session.pop('original_filename', None); session.pop('summary_stats', None); session.pop('min_year', None); session.pop('max_year', None)
    print("Session cleared for new upload.")
    return render_template_string(INDEX_HTML, title="Upload CSV", heading="Upload Transaction History", step=1, current_year_footer=datetime.datetime.now().year)

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files: flash('No file part in the request.', 'error'); return redirect(url_for('index'))
    file = request.files['file']
    if file.filename == '': flash('No file selected for uploading.', 'error'); return redirect(url_for('index'))
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename + "_proctemp_" + str(os.getpid()))
        try:
            file.save(filepath); print(f"File saved temporarily to: {filepath}")
            # time.sleep(1) # Simulate processing
            all_taxable_events, summary_stats, min_year, max_year = process_full_history(filepath)
            print(f"Processing complete. Events: {len(all_taxable_events)}, Min Year: {min_year}, Max Year: {max_year}")
            serializable_events = []
            for event in all_taxable_events:
                 event_copy = event.copy()
                 if isinstance(event_copy.get('date'), pd.Timestamp): event_copy['date'] = event_copy['date'].isoformat()
                 for key in ['amount', 'income', 'proceeds', 'cost_base', 'gain_loss']:
                    if key in event_copy and isinstance(event_copy[key], Decimal): event_copy[key] = str(event_copy[key])
                 serializable_events.append(event_copy)
            session['all_taxable_events'] = serializable_events
            session['original_filename'] = filename
            session['summary_stats'] = summary_stats
            session['min_year'] = min_year
            session['max_year'] = max_year
            session.modified = True
            print(f"Data stored in session for filename: {filename}")
            flash('File processed successfully. Please select the tax year.', 'success')
            return redirect(url_for('select_year'))
        except ValueError as e: flash(f"Error processing file: {e}", 'error'); print(f"ValueError during processing: {e}")
        except Exception as e: print(f"Unexpected upload/processing error: {traceback.format_exc()}"); flash(f"An unexpected error occurred: {e}", 'error')
        finally:
            if os.path.exists(filepath):
                try: os.remove(filepath); print(f"Temporary file removed: {filepath}")
                except OSError as e: print(f"Warning: Could not remove temporary file {filepath}: {e}")
        return redirect(url_for('index'))
    else: flash('Invalid file type. Only CSV files are allowed.', 'error'); return redirect(url_for('index'))

@app.route('/select_year', methods=['GET'])
def select_year():
    if 'all_taxable_events' not in session or 'min_year' not in session or 'max_year' not in session:
        flash('Processed data not found in session. Please upload the file again.', 'error'); print("Session data missing for /select_year"); return redirect(url_for('index'))
    filename = session.get('original_filename', 'Unknown')
    min_year_data = session.get('min_year'); max_year_data = session.get('max_year'); current_year = datetime.datetime.now().year
    if min_year_data is None or max_year_data is None or not isinstance(min_year_data, int) or not isinstance(max_year_data, int):
         flash('Error retrieving year range from processed data. Try uploading again.', 'error'); print(f"Invalid min/max year in session: {min_year_data}, {max_year_data}"); session.pop('all_taxable_events',None); session.pop('min_year',None); session.pop('max_year',None); return redirect(url_for('index'))
    potential_default = max_year_data
    if potential_default > current_year: potential_default = current_year
    default_year = max(min_year_data, potential_default)
    default_year = min(max_year_data, default_year)

    # Generate list of available years for the dropdown
    available_years = list(range(min_year_data, max_year_data + 1))
    # available_years.insert(0, "all") # Add "all" option - handled in template now

    print(f"Rendering select_year page. Min: {min_year_data}, Max: {max_year_data}, Default: {default_year}, Available: {available_years}")
    return render_template_string(SELECT_YEAR_HTML, title="Select Tax Year", heading="Select Tax Year", step=2, filename=filename, min_year=min_year_data, max_year=max_year_data, default_year=default_year, available_years=available_years, current_year_footer=datetime.datetime.now().year)

@app.route('/results', methods=['POST'])
def show_results():
    if 'all_taxable_events' not in session or 'min_year' not in session or 'max_year' not in session:
        flash('Session data expired or missing. Please upload the file again.', 'error')
        print("Session data missing for /results")
        return redirect(url_for('index'))

    min_year_data = session.get('min_year')
    max_year_data = session.get('max_year')
    current_real_year = datetime.datetime.now().year

    if min_year_data is None or max_year_data is None or not isinstance(min_year_data, int) or not isinstance(max_year_data, int):
        flash('Error retrieving valid year range from session. Please upload again.', 'error')
        print(f"Invalid min/max year in session during results: {min_year_data}, {max_year_data}")
        return redirect(url_for('index'))

    tax_year_str = request.form.get('tax_year')
    if tax_year_str is None:
        flash("Tax year selection not provided.", 'error')
        return redirect(url_for('select_year'))

    is_all_years_report = (tax_year_str == 'all')
    tax_year_display = "All Years" if is_all_years_report else tax_year_str # For titles/headings

    if not is_all_years_report:
        try:
            tax_year = int(tax_year_str)
            if not (min_year_data <= tax_year <= max_year_data):
                raise ValueError(f"Selected year {tax_year} is outside the valid range ({min_year_data}-{max_year_data}).")
        except (TypeError, ValueError) as e:
            flash(f'Invalid tax year selection: {e}.', 'error')
            print(f"Invalid tax year received: {request.form.get('tax_year')}. Error: {e}")
            return redirect(url_for('select_year'))
    else:
        tax_year = "all" # Use 'all' internally for logic/selection state

    all_taxable_events_serial = session.get('all_taxable_events', [])
    filename = session.get('original_filename', 'Unknown')
    summary_stats_global = session.get('summary_stats', {'total_transactions': 'N/A'})

    if not all_taxable_events_serial:
        flash('Processed transaction data is empty in session. Please upload again.', 'error')
        print("all_taxable_events_serial was empty.")
        return redirect(url_for('index'))

    all_taxable_events = []
    try:
        for event_data in all_taxable_events_serial:
            event = event_data.copy()
            if 'date' in event and isinstance(event['date'], str):
                try: event['date'] = pd.Timestamp(event['date'])
                except ValueError: print(f"Warning: Could not parse date '{event['date']}'. Skipping."); continue
            numeric_fields = ['amount', 'income', 'proceeds', 'cost_base', 'gain_loss']
            for field in numeric_fields:
                if field in event and event[field] is not None:
                    try: event[field] = Decimal(str(event[field]))
                    except (InvalidOperation, TypeError): print(f"Warning: Could not convert '{event[field]}' to Decimal for '{field}'. Using 0."); event[field] = Decimal(0)
            all_taxable_events.append(event)
    except Exception as e:
        print(f"Error deserializing session data: {traceback.format_exc()}")
        flash('Error reading processed data. Please try uploading again.', 'error')
        return redirect(url_for('index'))

    if not all_taxable_events:
        flash('Failed to load valid transaction data. Please upload again.', 'error')
        print("all_taxable_events empty after deserialization.")
        return redirect(url_for('index'))

    # Generate available years for the update dropdown on the results page
    available_years_for_update = list(range(min_year_data, max_year_data + 1))

    try:
        if is_all_years_report:
            print(f"Calculating aggregated report for years: {min_year_data}-{max_year_data}")
            # Initialize aggregated data structures
            aggregated_summary = {'total_gain_loss': Decimal(0), 'total_reward_income': Decimal(0)}
            aggregated_stats = {
                'disposition_count': 0, 'reward_count': 0,
                'total_proceeds': Decimal(0), 'total_cost_disposed': Decimal(0),
                'largest_gain': Decimal('-Infinity'), 'largest_loss': Decimal('Infinity'),
                'reward_breakdown': defaultdict(lambda: {'count': 0, 'value': Decimal(0)}),
                'assets_involved': set()
            }

            # Loop through each year in the range
            for year in range(min_year_data, max_year_data + 1):
                year_summary, year_stats_single, _, _ = calculate_report_for_year(all_taxable_events, year)

                # Aggregate results
                aggregated_summary['total_gain_loss'] += (year_summary['before_cutoff'] + year_summary['after_cutoff'])
                aggregated_summary['total_reward_income'] += year_summary['reward_income']

                aggregated_stats['disposition_count'] += year_stats_single['disposition_count']
                aggregated_stats['reward_count'] += year_stats_single['reward_count']
                aggregated_stats['total_proceeds'] += year_stats_single['total_proceeds']
                aggregated_stats['total_cost_disposed'] += year_stats_single['total_cost_disposed']
                aggregated_stats['largest_gain'] = max(aggregated_stats['largest_gain'], year_stats_single['largest_gain'])
                aggregated_stats['largest_loss'] = min(aggregated_stats['largest_loss'], year_stats_single['largest_loss'])
                aggregated_stats['assets_involved'].update(year_stats_single['assets_involved'])

                for reward_type, data in year_stats_single['reward_breakdown'].items():
                    aggregated_stats['reward_breakdown'][reward_type]['count'] += data['count']
                    aggregated_stats['reward_breakdown'][reward_type]['value'] += data['value']

            # Finalize aggregated stats
            if aggregated_stats['largest_gain'] == Decimal('-Infinity'): aggregated_stats['largest_gain'] = Decimal(0)
            if aggregated_stats['largest_loss'] == Decimal('Infinity'): aggregated_stats['largest_loss'] = Decimal(0)
            aggregated_stats['assets_involved'] = sorted(list(aggregated_stats['assets_involved']))
            aggregated_stats['reward_breakdown'] = {k: {'count': v['count'], 'value': quantize_decimal(v['value'], CURRENCY_PLACES)} for k, v in aggregated_stats['reward_breakdown'].items()}

            print(f"Aggregation complete for {min_year_data}-{max_year_data}.")
            return render_template_string(
                RESULTS_HTML,
                title=f"Tax Report {min_year_data}-{max_year_data}",
                heading=f"Aggregated Tax Report ({min_year_data}-{max_year_data})",
                step=3,
                tax_year="all", # Pass 'all' to template for selection logic
                is_all_years_report=True,
                aggregated_summary=aggregated_summary,
                aggregated_stats=aggregated_stats,
                dispositions_in_year=[], # Empty for all years view
                rewards_in_year=[],     # Empty for all years view
                filename=filename,
                summary_stats=summary_stats_global,
                min_year=min_year_data,
                max_year=max_year_data,
                available_years_for_update=available_years_for_update,
                current_year_footer=datetime.datetime.now().year
            )

        else: # Single year report
            print(f"Calculating report for year: {tax_year}")
            tax_summary, year_stats, dispositions_in_year, rewards_in_year = calculate_report_for_year(all_taxable_events, tax_year)
            print(f"Calculation complete for {tax_year}.")
            return render_template_string(
                RESULTS_HTML,
                title=f"Tax Report {tax_year}",
                heading=f"Tax Report for {tax_year}",
                step=3,
                tax_year=tax_year, # Pass the specific year
                is_all_years_report=False,
                tax_summary=tax_summary,
                year_stats=year_stats,
                dispositions_in_year=dispositions_in_year,
                rewards_in_year=rewards_in_year,
                aggregated_summary={}, # Empty for single year view
                aggregated_stats={},   # Empty for single year view
                filename=filename,
                summary_stats=summary_stats_global,
                min_year=min_year_data,
                max_year=max_year_data,
                available_years_for_update=available_years_for_update,
                current_year_footer=datetime.datetime.now().year
            )

    except Exception as e:
        print(f"Error calculating report for {tax_year_display}: {traceback.format_exc()}")
        flash(f"Error generating report for {tax_year_display}: {e}", 'error')
        # Redirect back to select_year, as results failed
        return redirect(url_for('select_year'))

# --- Main Execution ---
if __name__ == '__main__':
    for dir_path in [app.config['UPLOAD_FOLDER'], app.config['SESSION_FILE_DIR']]:
        if not os.path.exists(dir_path):
            try:
                os.makedirs(dir_path)
                print(f"Created directory: {dir_path}")
            except OSError as e:
                print(f"FATAL: Could not create directory {dir_path}: {e}")
                exit(1)
    # Set debug=False for production!
    app.run(debug=True, host='0.0.0.0', port=5000)

