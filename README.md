Internet Banking Website

Overview

This is a secure and user-friendly internet banking website that allows users to perform various banking operations online. The platform is built using HTML, CSS, and JavaScript for the frontend, Node.js for the backend, and MySQL for data storage.

Features

User Authentication: Secure login and registration system.

Account Management: View account details, balances, and transaction history.

Funds Transfer: Transfer money between accounts securely.

Bill Payments: Pay utility bills and other services.

Transaction History: Track past transactions with detailed records.

Security: Implemented encryption and authentication measures.

Technologies Used

Frontend: HTML, CSS, JavaScript

Backend: Node.js, Express.js

Database: MySQL

Security: JWT Authentication, bcrypt for password hashing

Installation

Prerequisites

Ensure you have the following installed:

Node.js

MySQL

Steps

Clone the repository:

git clone https://github.com/your-username/internet-banking.git
cd internet-banking

Install dependencies:

npm install

Configure the database:

Create a MySQL database.

Import the provided SQL schema.

Update database credentials in the .env file.

Start the server:

npm start

Open the application in the browser:

http://localhost:3000

API Endpoints

Method

Endpoint

Description

POST

/api/register

User registration

POST

/api/login

User login

GET

/api/account

Get account details

POST

/api/transfer

Transfer funds

GET

/api/transactions

Get transaction history

Security Measures

JWT Authentication for secure API access.

Bcrypt Hashing for storing passwords securely.

SSL/TLS to encrypt data transmission (to be configured in production).

Future Enhancements

Add two-factor authentication.

Implement AI-based fraud detection.

Develop a mobile-friendly version.

Contributing

Contributions are welcome! Please fork the repository and submit a pull request.

License

This project is licensed under the MIT License.

