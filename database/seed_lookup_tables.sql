-- ============================================================================
-- Seed Data: Lookup Tables
-- These tables can only be modified by superuser
-- ============================================================================

-- Positions
INSERT INTO public.positions (id, name, phone, employment_type, notes) VALUES
(1, 'Instructor', '+1-202-555-0101', 'Full-time', 'Lead driving instructor'),
(2, 'Senior Instructor', '+1-202-555-0102', 'Full-time', 'Office and training lead'),
(3, 'Assistant Instructor', '+1-202-555-0103', 'Part-time', 'Support instructor'),
(4, 'Administrator', '+1-202-555-0104', 'Full-time', 'Office administrator'),
(5, 'Coordinator', '+1-202-555-0105', 'Full-time', 'Schedule coordinator'),
(6, 'Mechanic', '+1-202-555-0106', 'Part-time', 'Vehicle maintenance'),
(7, 'Dispatcher', '+1-202-555-0107', 'Full-time', 'Routes and logistics'),
(8, 'Customer Service', '+1-202-555-0108', 'Full-time', 'Student support'),
(9, 'Training Manager', '+1-202-555-0109', 'Full-time', 'Program manager'),
(10, 'Office Assistant', '+1-202-555-0110', 'Part-time', 'Administrative assistant')
ON CONFLICT (id) DO NOTHING;

SELECT setval('public.positions_id_seq', (SELECT MAX(id) FROM public.positions));

-- Lesson Formats
INSERT INTO public.lesson_formats (id, name) VALUES
(1, 'Classroom'),
(2, 'Online'),
(3, 'On-road'),
(4, 'Mixed')
ON CONFLICT (id) DO NOTHING;

SELECT setval('public.lesson_formats_id_seq', (SELECT MAX(id) FROM public.lesson_formats));

-- Locations
INSERT INTO public.locations (id, geolocation, location_type, address, responsible_employee_id) VALUES
(1, '38.8977,-77.0365', 'Classroom', '123 School St, Washington, DC', 1),
(2, '34.0522,-118.2437', 'Classroom', '456 Training Ave, Los Angeles, CA', 2),
(3, '41.8781,-87.6298', 'Classroom', '789 Practice Blvd, Chicago, IL', 3),
(4, '29.7604,-95.3698', 'Computer Lab', '101 Digital Rd, Houston, TX', 4),
(5, '40.7128,-74.0060', 'Workshop', '202 Service Ln, New York, NY', 5),
(6, '47.6062,-122.3321', 'Auditorium', '303 Lecture Way, Seattle, WA', 6),
(7, '39.9526,-75.1652', 'Driving Range', '404 Practice Dr, Philadelphia, PA', 7),
(8, '37.7749,-122.4194', 'Online Platform', 'Virtual Classroom (Zoom/Webex)', 8),
(9, '33.4484,-112.0740', 'Outdoor Track', '505 Track Rd, Phoenix, AZ', 1),
(10, '32.7767,-96.7970', 'Classroom', '606 Study Cir, Dallas, TX', 2)
ON CONFLICT (id) DO NOTHING;

SELECT setval('public.locations_id_seq', (SELECT MAX(id) FROM public.locations));

-- Vehicles
INSERT INTO public.vehicles (id, vehicle_number, route, notes, category) VALUES
(1, 'D001', 'Downtown loop', 'Clean and serviced', 'B'),
(2, 'D002', 'Highway route', 'New tires installed', 'B'),
(3, 'D003', 'Suburban route', 'Needs oil change soon', 'B'),
(4, 'D004', 'Practice circuit', 'Ready for lessons', 'C'),
(5, 'D005', 'City route', 'Brake inspection complete', 'B'),
(6, 'D006', 'Night training', 'Equipped with safety kit', 'B'),
(7, 'D007', 'Combined route', 'Fuel-efficient model', 'B,C'),
(8, 'D008', 'Main highway', 'Air conditioning works', 'B'),
(9, 'D009', 'Intercity route', 'Recent maintenance', 'C'),
(10, 'D010', 'Safety route', 'Fully insured', 'B')
ON CONFLICT (id) DO NOTHING;

SELECT setval('public.vehicles_id_seq', (SELECT MAX(id) FROM public.vehicles));

-- Groups
INSERT INTO public.groups (id, group_number, room_number, format_type) VALUES
(1, 'GR-101', '101', 'Classroom'),
(2, 'GR-102', '102', 'Classroom'),
(3, 'GR-201', '201', 'Mixed'),
(4, 'GR-202', '202', 'Classroom'),
(5, 'GR-301', '301', 'Online'),
(6, 'GR-302', '302', 'Classroom'),
(7, 'GR-401', '401', 'On-road'),
(8, 'GR-402', '402', 'Mixed'),
(9, 'GR-501', '501', 'Classroom'),
(10, 'GR-502', '502', 'Online')
ON CONFLICT (id) DO NOTHING;

SELECT setval('public.groups_id_seq', (SELECT MAX(id) FROM public.groups));
