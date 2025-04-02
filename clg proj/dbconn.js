import {createPool} from "mysql2";
import dotenv from "dotenv";
dotenv.config();

const pool = createPool({
    host: process.env.MYSQL_HOST,
    user: process.env.MYSQL_USER,
    password: process.env.MYSQL_PASSWORD,
    database: process.env.MYSQL_DATABASE,
}).promise();
export async function CreateUser(name, email, password){
    const result=await pool.query(`INSERT INTO USER(NAME,EMAIL,PASSWORD) VALUES
    (?,?,?)`,[name,email,password]);
    return console.log(result[0]);
}
export async function CheckUser(email,password){
    try{
    const result=await pool.query(`
        SELECT * FROM USER
        WHERE EMAIL=?
        `, [email]);
        return result[0];   
    }catch(err){
        console.log(err);
        return false;
    }
}