# Invoice Generator

A production-ready FastAPI application for generating PDF invoices, managing invoice history, and simulating email delivery.

## Features

-   **Dashboard**: Create new invoices and view history log.
-   **PDF Generation**: Server-side PDF generation using `xhtml2pdf`.
-   **Data Persistence**: SQLite database storage.
-   **Email Simulation**: Console logging for email actions.
-   **Docker Ready**: Simple deployment with Docker.

## Running Locally

1.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

2.  **Run Application**:
    ```bash
    python main.py
    ```

3.  **Access**:
    Open [http://localhost:8000](http://localhost:8000) in your browser.

## Running with Docker

1.  **Build Image**:
    ```bash
    docker build -t invoice-app .
    ```

2.  **Run Container**:
    ```bash
    docker run -p 8000:8000 -v $(pwd)/data:/app/data invoice-app
    ```
    *Note: Mounting the volume ensures the database and generated PDFs persist.*

## Implementation Details

-   **Framework**: FastAPI
-   **Database**: SQLite with SQLAlchemy
-   **Template Engine**: Jinja2
-   **PDF Engine**: xhtml2pdf

## Note

Email sending is currently **simulated**. Check the application console logs to see the "email sent" confirmation details.
