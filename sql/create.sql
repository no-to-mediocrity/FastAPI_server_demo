DO $$ 
BEGIN 
    CREATE TABLE IF NOT EXISTS projects (
        id SERIAL PRIMARY KEY,
        name VARCHAR(255) UNIQUE NOT NULL
    );

    CREATE TABLE IF NOT EXISTS project_data (
        project_id INT NOT NULL,
        year INT,
        cost DECIMAL(10, 2) NOT NULL,
        PRIMARY KEY (project_id, year),
        FOREIGN KEY (project_id) REFERENCES projects(id)
    );
END $$;
