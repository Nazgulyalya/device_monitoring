from flask import Flask, request, jsonify
import psycopg2

app = Flask(__name__)

DB_CONFIG = {
    "host": "localhost",
    "port": "5432",
    "database": "device_monitoring",
    "user": "your_username",
    "password": "your_password"
}

def connect_db():
    return psycopg2.connect(**DB_CONFIG)
    
def create_db():
    conn = connect_db()
    if not conn:
        return
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS device_info (
            id SERIAL PRIMARY KEY,
            owner TEXT,
            internal_ip TEXT,
            external_ip TEXT,
            mac_address TEXT,
            cpu TEXT,
            cpu_model_name TEXT,
            ram TEXT,
            storage TEXT,
            os TEXT,
            os_installation_date TEXT,
            manufacturer TEXT,
            model TEXT,
            battery_status TEXT,
            serial_number TEXT, 
            service_tag TEXT,         
            last_updated TIMESTAMP DEFAULT now()
        );
    ''')
    conn.commit()
    cursor.close()
    conn.close()
    print("[INFO] Таблица device_info проверена/создана.")


@app.route("/report", methods=["POST"])
def report():
    device_info = request.json
    if not device_info:
        return jsonify({"error": "No data received"}), 400

    try:
        conn = connect_db()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO device_info (owner, internal_ip, external_ip, mac_address, cpu, cpu_model_name, 
            ram, storage, os, os_installation_date, manufacturer, model, battery_status, serial_number, service_tag, last_updated)
            VALUES (%s, %s, %s, %s, 
                    %s, %s, %s, %s, 
                    %s, %s, %s, %s, 
                    %s, %s, %s, now() AT TIME ZONE 'Asia/Almaty');
        ''', (
            device_info["Owner"], device_info["Internal_IP"], device_info["External_IP"],
            device_info["MAC"], device_info["CPU"], device_info["CPU_Model_Name"],
            device_info["RAM"], device_info["Storage"], device_info["OS"], 
            device_info["OS_Installation_Date"], device_info["Manufacturer"],
            device_info["Model"], device_info["Battery_Status"], device_info["Serial_Number"],
            device_info["Service_Tag"]
        ))
        print("[INFO] Новая запись добавлена")

        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({"message": "Data saved successfully"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    create_db()
    app.run(host="0.0.0.0", port=5000, debug=True)

