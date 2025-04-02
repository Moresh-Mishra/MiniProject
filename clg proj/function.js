import express from "express";
import { fileURLToPath } from "url";
import { dirname } from "path";
import { CreateUser, CheckUser } from "./dbconn.js";
import bcrypt from "bcrypt";
import bodyParser from "body-parser";
import jwt from "jsonwebtoken";
import cookieParser from "cookie-parser";

const __dirname = dirname(fileURLToPath(import.meta.url));
const app = express();
const port = 3000;
const saltRounds = 10;
const secret = "connect.sid";

app.use(express.static("public"));
app.use(bodyParser.urlencoded({ extended: true }));
app.use(express.json());
app.use(cookieParser());
app.use((req, res, next) => {
  res.setHeader(
    "Cache-Control",
    "no-store, no-cache, must-revalidate, private"
  );
  res.setHeader("Pragma", "no-cache");
  res.setHeader("Expires", "0");
  res.setHeader("Surrogate-Control", "no-store");
  next();
});

app.get("/dashboard", (req, res) => {
    const token = req.cookies.token;
    if (!token) {
        return res.redirect('/login');
    }
    jwt.verify(token, secret, (err, decoded) => {
        if (err) {
            console.log(err);
            return res.redirect('/login');
        }
        res.sendFile(__dirname + "/public/index.html");
    });
});

app.get("/login", (req, res) => {
  res.sendFile(__dirname + "/public/login.html");
});
let name = "",
  email = "",
  password = "";
  
app.post("/register", (req, res) => {
  res.sendFile(__dirname + "/public/register.html");
  email = req.body["email"];
  password = req.body["password"];
  name = req.body["name"];
  bcrypt.hash(password, saltRounds, (err, hash) => {
    if (err) {
      console.log(err);
    } else {
      CreateUser(name, email, hash);
    }
  });
  res.redirect("/login");
});

app.post("/submit", async (req, res) => {
  try {
    email = req.body["email"];
    password = req.body["password"];

    const user = await CheckUser(email);
    const name= user[0].NAME;
    const HashedPassword = user[0].PASSWORD;
    bcrypt.compare(password, HashedPassword, (err, ans) => {
      if (err) {
        console.error("Error while comparing passwords:", err);
        return res.status(500).json({ message: "Internal server error" });
      }

      if (ans) {
        const token = jwt.sign({ user: email, name: name }, secret, { expiresIn: 3600 });
        res.cookie("token", token, { httpOnly: true, secure: true });
        res.redirect("/dashboard");
      } else {
        res.redirect("/login");
      }
    });
  } catch (error) {
    console.error("Error:", error);
    return res.status(500).json({ message: "Internal server error" });
  }
});

app.post("/logout", (req, res) => {
  const token = req.cookies.token;
  if (!token) return res.status(400).json({ message: "Token required" });
  res.cookie("token", "", { maxAge: 1 });
  res.setHeader("Cache-Control", "no-store, no-cache, must-revalidate, private");
  res.setHeader("Pragma", "no-cache");
  res.setHeader("Expires", "0");
  res.redirect("/login");
});

app.get("/getUserName", (req, res) => {
  const token = req.cookies.token;
  if (!token) {
    return res.json({ name: null });
  }

  jwt.verify(token, secret, (err, decoded) => {
    if (err) {
      return res.json({ name: null });
    }

    res.json({ name: decoded.name });
  });
});


app.listen(port, () => {
  console.log(`Server is running on port ${port}`);
});
