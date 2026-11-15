SELECT 
    st.store_id,
    st.store_name,
    st.city,
    st.region,
    
    COUNT(DISTINCT CASE WHEN de.is_pharmacist = TRUE THEN de.employee_id END) AS pharmacist_count,
    
    COUNT(DISTINCT de.employee_id) AS total_staff_count,
    
    TO_CHAR(COUNT(fp.prescription_id), 'FM999,999,990') AS total_prescriptions,
    
    ROUND(
        COUNT(fp.prescription_id)::NUMERIC / 
        NULLIF(COUNT(DISTINCT CASE WHEN de.is_pharmacist = TRUE THEN de.employee_id END), 0), 2
    ) AS prescriptions_per_pharmacist

FROM dim_stores st
LEFT JOIN dim_employees de ON st.store_id = de.store_id
LEFT JOIN fact_prescriptions fp ON st.store_id = fp.store_id
GROUP BY st.store_id, st.store_name, st.city, st.region
ORDER BY prescriptions_per_pharmacist DESC;








WITH StorePayroll AS (
    SELECT 
        store_id,
        SUM(salary) AS total_payroll,
        COUNT(employee_id) AS total_staff_count,
        COUNT(CASE WHEN is_pharmacist = TRUE THEN 1 END) AS pharmacist_count
    FROM dim_employees
    GROUP BY store_id
),
StoreWorkload AS (
    SELECT 
        store_id,
        COUNT(prescription_id) AS total_prescriptions
    FROM fact_prescriptions
    GROUP BY store_id
)
SELECT 
    st.store_id,
    st.store_name,
    st.city,
    st.region,
    COALESCE(sp.total_staff_count, 0) AS total_staff_count,
    COALESCE(sp.pharmacist_count, 0) AS pharmacist_count,
    
    ROUND(COALESCE(sp.total_payroll, 0)::NUMERIC, 2) AS total_store_payroll,
    COALESCE(sw.total_prescriptions, 0) AS total_prescriptions,
    
    ROUND(
        COALESCE(sp.total_payroll, 0)::NUMERIC / NULLIF(sw.total_prescriptions, 0), 2
    ) AS labor_cost_per_prescription,
    
    ROUND(
        COALESCE(sw.total_prescriptions, 0)::NUMERIC / 
        NULLIF(COALESCE(sp.pharmacist_count, 0), 0), 2
    ) AS prescriptions_per_pharmacist

FROM dim_stores st
LEFT JOIN StorePayroll sp ON st.store_id = sp.store_id
LEFT JOIN StoreWorkload sw ON st.store_id = sw.store_id
ORDER BY labor_cost_per_prescription ASC;