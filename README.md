
### 📦 Smart Inventory System – Complete Web App for Small Business Management

**Smart Inventory System** is a full-featured inventory and account management platform built using **Python (Flask)** and **MySQL**, with a responsive, modern UI powered by **HTML, CSS, and Jinja2**.

It is designed specifically for **individual sellers**, **small businesses**, and **freelancers** who want to maintain a digital inventory system **without paying for hosting or expensive ERP solutions**.

This system offers:

---

### ✅ Key Features:

* 🔐 **User Authentication System**

  * Register and login securely with **Flask-WTF**
  * Passwords are hashed using **bcrypt**
  * **Google OAuth Login** via **Flask-Dance** (Facebook login is marked as *coming soon*)

* 🧾 **User Dashboard**

  * Personalized dashboard with **user information**, **profile editing**, and **logout**
  * Upload and display **profile pictures**
  * Change password securely (except for Google login users)

* 📊 **Inventory/Product Management**

  * Add, edit, delete, and view products with category and stock info
  * Track total products and unique categories
  * Products are linked to individual users

* 🌐 **Front-End Experience**

  * Custom UI using **HTML5, CSS3**, and **Jinja2 templates**
  * Responsive layout with modern cards, alerts, and section toggling
  * Fully themed **dashboard UI with sidebar and stats**

* 📮 **Contact & Messaging**

  * Users can send messages via contact page
  * Messages are shown as flash notifications (or can be stored in DB)

* 📤 **Image Upload**

  * Upload and store profile images in `/static/uploads`
  * Secure file handling using Flask’s `request.files`

---

### 🛠️ Tech Stack:

| Layer            | Tools Used                                      |
| ---------------- | ----------------------------------------------- |
| **Frontend**     | HTML, CSS, JavaScript, Jinja2                   |
| **Backend**      | Python (Flask), Flask-WTF, Flask-Dance          |
| **Database**     | MySQL (via flask-mysqldb)                       |
| **Auth**         | Custom login system + Google OAuth2             |
| **Security**     | bcrypt for password hashing, CSRF via Flask-WTF |
| **Image Upload** | Secure file upload to static folder             |

---

### 🌍 Accessibility & Hosting:

This project is built for **local use** but can be shared over the internet using **Ngrok** — a simple tool to create a secure tunnel to your localhost.

No cloud hosting or domain is required to share this project with others.

---

### 🔧 Ideal For:

* Shop owners and home-based sellers needing to track products
* Freelancers managing small-scale product inventories
* Students learning **Flask + MySQL integration**
* Anyone looking to deploy an inventory system *without* monthly charges

---

### 🔒 Coming Soon:

* Facebook Login
* Forgot Password with Email Reset
* Product image gallery
* Excel export for reports

---

