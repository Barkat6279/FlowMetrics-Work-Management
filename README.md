# FlowMetrics — Team Work Management Platform

FlowMetrics is a role-based work management application designed to help teams assign tasks, monitor progress, manage projects, and improve collaboration through a centralized workspace.

## Overview

The application provides separate workspaces for administrators, team leaders, and employees, with role-based access to relevant tasks and management features.

## Key Features

- **Role-Based Access:** Separate Admin, Team Leader, and Employee workspaces.
- **Task Management:** Create, assign, update, and track tasks.
- **Project Management:** Organize work around projects and teams.
- **Progress Tracking:** Monitor task status and completion.
- **Employee Management:** Manage team members and assignments.
- **Daily Reports:** Record and review work updates.
- **Notifications:** Keep users informed about relevant activity.

## Technology Stack

| Layer | Technologies |
|---|---|
| Frontend | React, JavaScript, CSS |
| Build Tool | Vite |
| Backend | Python |
| Database | SQLite |
| Version Control | Git, GitHub |

## Project Structure

```text
FlowMetrics/
├── backend/
│   ├── main.py
│   ├── requirements.txt
│   └── flowmetrics.db
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── main.jsx
│   │   └── styles.css
│   ├── package.json
│   └── index.html
├── README.md
├── LICENSE
└── .gitignore
```

## Run Locally

### 1. Clone the repository

```bash
git clone https://github.com/Barkat6279/FlowMetrics-Work-Management.git
cd FlowMetrics-Work-Management
```

### 2. Start the backend

```bash
cd backend
py main.py
```

### 3. Start the frontend

Open a second terminal:

```bash
cd frontend
npm install
npm.cmd run dev
```

Open the local URL displayed by Vite in your browser.

## Application Screenshots

Screenshots of the login page, dashboards, task management, and project workflows will be added here.

## Future Improvements

- Cloud deployment
- Automated testing
- Enhanced reporting and analytics
- Improved notification workflows

## Author

**Barkat**

GitHub: https://github.com/Barkat6279

---

## License

This project is licensed under the MIT License.
