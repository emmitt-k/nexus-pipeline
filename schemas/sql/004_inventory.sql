-- Inventory master table
CREATE TABLE inventory (
    id SERIAL PRIMARY KEY,
    sku VARCHAR(100),
    location VARCHAR(100),
    quantity INTEGER NOT NULL,
    reserved_quantity INTEGER DEFAULT 0,
    available_quantity INTEGER,
    last_restocked DATE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_inventory_sku ON inventory(sku);
CREATE INDEX idx_inventory_location ON inventory(location);
CREATE INDEX idx_inventory_available ON inventory(available_quantity);

-- Foreign key after table exists
ALTER TABLE inventory ADD CONSTRAINT fk_inventory_product
    FOREIGN KEY (sku) REFERENCES products(sku);