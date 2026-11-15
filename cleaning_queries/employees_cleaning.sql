SELECT*
FROM employees;

SELECT 
    COUNT(*) AS total_rows,
    COUNT(*) - COUNT(employee_id) AS missing_employee_id,
    COUNT(*) - COUNT(store_id) AS missing_store_id,
    COUNT(*) - COUNT(employee_name) AS missing_employee_name,
    COUNT(*) - COUNT(email) AS missing_email,
    COUNT(*) - COUNT(position) AS missing_position,
    COUNT(*) - COUNT(salary) AS missing_salary,
    COUNT(*) - COUNT(hire_date) AS missing_hire_date,
    COUNT(*) - COUNT(is_pharmacist) AS missing_is_pharmacist
FROM employees;

SELECT 
    employee_id, 
    COUNT(*) AS duplicate_count
FROM employees
GROUP BY employee_id
HAVING COUNT(*) > 1;

SELECT position, is_pharmacist
FROM employees;

ALTER TABLE employees
DROP COLUMN is_pharmacist;

ALTER TABLE employees
ADD COLUMN is_pharmacist BOOLEAN 
GENERATED ALWAYS AS (position = 'Pharmacist') STORED;

