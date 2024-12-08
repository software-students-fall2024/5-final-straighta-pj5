# Final Project

An exercise to put to practice software development teamwork, subsystem communication, containers, deployment, and CI/CD pipelines. See [instructions](./instructions.md) for details.

![Webapp CI/CD](https://github.com/software-students-fall2024/5-final-straighta-pj5/actions/workflows/webapp.yml/badge.svg)
[![log github events](https://github.com/software-students-fall2024/5-final-straighta-pj5/actions/workflows/event-logger.yml/badge.svg)](https://github.com/software-students-fall2024/5-final-straighta-pj5/actions/workflows/event-logger.yml)

---
## **Project Overview**
The Financial Tracker Web Application is designed to help users manage their finances by providing a seamless interface to track expenses, set budgets, and visualize spending habits. The application allows users to securely log in, add expenses, edit them, set monthly budgets, and analyze spending through intuitive visualizations.

## **Features**
- User Authentication: Secure login and profile management.
- Expense Management: Add, edit, and view expenses by category.
- Budget Setting: Set monthly budgets with alerts for budget overruns.
- Data Visualization: Dynamic charts to analyze daily, weekly, or monthly expenses.
- Database Integration: MongoDB stores user data, expenses, and budgets.

---

## **Subsystems**
The project consist of two main subsystems, each have its DockerFile:

### **1. Web**:
- **Technology**: Python(Flask)
- **Functionality**: Allow user to complete the above features.
- **Code Location**: `WebApp/.`
### **2. Mongo**
- **Technology**: MongoDB Database
- **Functionality**: Acts as the database for storing uploaded images and analysis results.

## Instruction to Run the Project

1. **Pre-requisites**
- Docker and Docker Compose installed.
- Access to MongoDB Atlas or a local MongoDB instance.
- Install python: 
    -   Make sure Python 3.8 or higher is installed on your system. You can download it from python.org.

2. **Clone the Repository**
```bash
git clone https://github.com/software-students-fall2024/5-final-straighta-pj5
cd 5-final-straighta-pj5
```
3. **Set up Virtual Environment**
- Run the following commands to create and activate the virtual environment:
```bash
python3 -m venv venv
```
or
```bash
python -m venv venv
```
- Activate the virtual environment:
    - On Windows:
    ```bash
    .\venv\Scripts\activate
    ```
    - On Mac:
    ```bash
    source venv/bin/activate
    ```

4. **Run Locally**
- Install Dependencies:
    - Use the requirements.txt file to install the necessary Python libraries:
    ```bash
    pip install -r WebApp/requirements.txt
    ```
- Run the app:
    ```bash
    python WebApp/app.py
    ```

5. **Run Docker**
   - You can build and start docker by: 
   ```bash
   docker-compose up --build
   ```
   - If any container has name conflicts (my-mongo):
      - stop the old containter by:
      ```bash
      docker stop mongo
      ```
      - After stopping, remove it with:
      ```bash
      docker rm mongo
      ```

6. **Access the Application**
   - Open a web browser and go to `http://127.0.0.1:3000/` 
   This will take you to the login page.

7. **Deactivate the Virtual Environment (Optional)**
   - When finished, deactivate the virtual environment by typing:
     ```bas
     deactivate
     ```

8. **Deployed Website**
   - http://159.203.104.236:3000

9. **Contributing**
   - Fork the repository.
   - Create a new branch for your feature:
   ```bash
   git checkout -b feature/your-feature
   ```
   - Commit and push your changes
   ```bash
   git commit -m "Add your feature"
   git push origin feature/your-feature
   ```
   - Open a pull request on GitHub.


## **Team Members**
- [Elaine Lyu](https://github.com/ElaineR02)
- [Linda Li](https://github.com/Applejam-ovo)
- [Rita He]( https://github.com/ritaziruihe)
- [Hannah Liang](https://github.com/HannahLiang627)

---
