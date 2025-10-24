# GNSS_Convertor
A GUI Tool for GNSS Data Download and Conversion gor Bernese Processing

A Python-based automation tool developed to download and preprocess GNSS CORS data from NASA’s CDDIS archive for use in Bernese GNSS software.

This project was built as part of my work at NRSC (ISRO) to simplify and speed up the daily data handling process for GNSS stations.

# Features

Automated Data Download – Fetches daily GNSS RINEX data files from NASA’s CDDIS archive.

Proxy & Authentication Support – Works in secure networks using proxy and .netrc or cookie-based login.

Automatic Conversion – Handles .crx.gz to .rnx and final file naming based on RINEX conventions.

Error Handling & Logging – Skips incomplete or invalid downloads and logs all activities.

Multi-threaded Execution – Runs multiple downloads in parallel to save time.

GUI Interface – Simple and clean Tkinter interface for easy use by non-programmers.

# How It Works

User enters:

NASA Earthdata credentials

Year and Month for data

Output directory

(Optional) Proxy credentials

The tool:

Logs into the NASA CDDIS archive using cookies or .netrc authentication.

Downloads .crx.gz files for selected GNSS stations.

Decompresses, converts, and renames files to standard RINEX format.

Deletes invalid or incomplete files automatically.

# Technologies Used

Python – Core programming language

Tkinter – For the graphical user interface

subprocess, gzip, shutil, threading – For automation and parallel execution

curl – For secure and authenticated data transfer

# What I Learned

Practical use of Python automation and scripting in a real scientific workflow.

Handling network-based authentication and proxy systems.

Improving performance using multi-threading and error handling.

Collaborating between Python automation and scientific tools like Bernese GNSS.

# About the Developer

I’m a Computer Science Engineering graduate (2024) working as a Technical Support Engineer (Contract) at NRSC, ISRO.

My focus is on Python development, data automation, and system troubleshooting for data workflows.
