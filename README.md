
# 🚦 Traffic Simulator

A modular and extensible Traffic Simulation System built in Python that models real-world traffic flow, signal control strategies, and emergency vehicle handling using multiple algorithmic approaches.

## 📌 Overview

This project simulates traffic movement across intersections by combining:

- 🚗 Vehicle behavior modeling
- 🚦 Intelligent traffic signal control
- ⚡ Emergency vehicle preemption
- 📊 Algorithm-based optimization (Greedy, DP, Fixed strategies)

The system is designed with a clean architecture, separating logic into independent modules for scalability and experimentation.

## ✨ Key Features

- **🚦 Traffic Signal Control Algorithms**
    - Greedy approach
    - Dynamic Programming-based optimization
    - Fixed timing strategy

- **🚗 Vehicle Simulation Engine**
    - Real-time vehicle movement logic
    - Intersection handling

- **🚑 Emergency Vehicle Preemption**
    - Priority-based signal override system

- **🌗 Time-based Traffic Profiles**
    - Traffic variation based on time of day

- **🎨 UI Rendering Layer**
    - Visual simulation output using renderer module

- **🧩 Highly Modular Design**
    - Easy to extend with new algorithms or features

## 🛠️ Tech Stack

**Language:** Python 🐍

**Core Concepts:**
- Object-Oriented Programming (OOP)
- Algorithm Design (Greedy, Dynamic Programming)
- Simulation Modeling
- Modular Architecture

## 📂 Project Structure

```
traffic-simulator/
├── algorithms/        # Traffic signal optimization algorithms
│   ├── dp_graph.py
│   ├── fixed.py
│   └── greedy.py
├── core/              # Core simulation logic
│   ├── intersection.py
│   └── vehicle.py
├── emergency/         # Emergency vehicle handling
│   └── preemption.py
├── profiles/          # Traffic patterns (time-based)
│   └── time_of_day.py
├── ui/                # Visualization layer
│   └── renderer.py
├── config.py          # Configuration settings
├── main.py            # Entry point
├── req.txt            # Dependencies
└── .gitignore
```

## ⚙️ Installation & Setup

1. **Clone the repository**
     ```bash
     git clone https://github.com/atharvadk/traffic-simulator.git
     cd traffic-simulator
     ```

2. **Create virtual environment (recommended)**
     ```bash
     python -m venv venv
     source venv/bin/activate   # Linux/Mac
     venv\Scripts\activate      # Windows
     ```

3. **Install dependencies**
     ```bash
     pip install -r req.txt
     ```

4. **Run the simulator**
     ```bash
     python main.py
     ```

## ▶️ How It Works

1. Vehicles are generated and assigned routes
2. Intersections manage traffic signals
3. Algorithms decide signal timing:
     - **Greedy** → quick local optimization
     - **DP** → optimized global decisions
     - **Fixed** → baseline comparison
4. Emergency vehicles override normal flow
5. Renderer displays simulation output

## 🧠 Algorithms Used

| Algorithm | Description |
|-----------|-------------|
| Greedy | Makes locally optimal decisions for signal switching |
| Dynamic Programming | Computes optimal signal timing over time |
| Fixed | Uses predefined signal intervals |

## 🚀 Future Enhancements

- 🤖 AI/ML-based traffic prediction
- 🌍 Real-world map integration
- 📊 Analytics dashboard
- 🚗 Multi-lane & highway simulation
- 🌐 Web-based visualization

## 🤝 Contributing

Contributions are welcome!

1. Fork the repository
2. Create a new branch (`feature/new-feature`)
3. Commit your changes
4. Push and create a Pull Request
