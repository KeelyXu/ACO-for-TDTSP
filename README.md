# Theme Park Route Optimizer: ACO for TDTSP

**Tired of spending hours in queues instead of enjoying rides?** This project uses **Ant Colony Optimization (ACO)** to solve one of the biggest challenges in theme park visits: finding the optimal route that minimizes your total time spent waiting, walking, and playing.

Long queue times are a major pain point that can significantly diminish your theme park experience. By intelligently scheduling your visit order based on real-world queue data, this tool helps you make the most of your day—whether you're visiting Shanghai Disneyland (we take this as an example), Universal Studios, or any other park available on [queue-times.com](https://queue-times.com/).

The algorithm abstracts this challenge into a **Time-Dependent Traveling Salesman Problem (TDTSP)**, calculating the optimal visitation sequence that adapts to changing wait times throughout the day.

The core algorithm is based on the research paper:

> Tomanová, P., & Holý, V. (2020, March). Ant colony optimization for time-dependent travelling salesman problem. In *Proceedings of the 2020 4th International Conference on Intelligent Systems, Metaheuristics & Swarm Intelligence* (pp. 47-51).



## 📖 Background & Problem Statement

### The Challenge: Dynamic Queue Times

In theme parks, waiting times for attractions fluctuate dramatically throughout the day. A ride that has a 20-minute wait in the morning might have a 90-minute wait in the afternoon. This variability makes route planning crucial—the order in which you visit attractions can make the difference between a smooth, enjoyable day and one spent mostly in lines.

The problem has two key components:

- **Static Cost:** Walking time between attractions is relatively fixed.
- **Dynamic Cost:** Queuing time depends heavily on *when* you arrive at each attraction.

Visitors want to visit a set of $N$ attractions starting from a specific location at a specific time and find a route that minimizes the total time spent (walking + waiting + playing).

### The Mathematical Model: TDTSP

This scenario is a classic example of the **Time-Dependent Traveling Salesman Problem (TDTSP)**.

Unlike the classical TSP where edge weights are constant, in TDTSP, the cost (weight) of an edge depends on the time at which the edge is traversed.

- **Nodes ($i, j$):** Attractions.
- **Time ($t$):** The current time of day.
- **Cost ($C_{ij}(t)$):** The cost to move from attraction $i$ to $j$ starting at time $t$.

In this project, the cost function is defined as:

$$Cost_{ij}(t) = T_{travel}(i, j) + T_{wait}(j, t + T_{travel}) + T_{play}(j)$$

Since the "cost" (waiting time) changes dynamically based on the arrival time, the TDTSP is computationally more demanding than the classical TSP.



## ⚙️ Algorithm & Methodology

### 1. Ant Colony Optimization (ACO) Framework

Inspired by how real ants find the shortest path to food, the algorithm simulates a colony of artificial ants exploring different routes through the park. Each ant makes decisions using a sophisticated probability function that balances three "senses":

- **Sense of Smell ($\alpha$):** Response to global pheromones ($F$) deposited by previous ants.
- **Sense of Sight ($\beta$):** Response to heuristic information (inverse of the time cost).
- **Sense of Taste ($\gamma$):** Response to "Local Pheromones" ($LF$), which only considers the immediate neighborhood ($LR$) of the path.

### 2. Four Optimization Stages

As described in the paper, the optimization process is divided into 4 distinct stages to prevent premature convergence and encourage exploration:

1. **Init:** High randomness to explore the search space.
2. **Main:** Balanced exploration and exploitation.
3. **Stagnate:** Triggered if the solution doesn't improve for `stagnCounter` iterations; introduces randomness to escape local optima.
4. **Final:** Focuses on refining the best solution found so far.

### 3. Four Types of Ants

The system utilizes heterogeneous agents (ants) with different behaviors:

- **Random:** Selects next node completely randomly (good for exploration).
- **Stochastic:** Selects based on probability derived from pheromones and costs.
- **Deterministic:** Always chooses the node with the highest probability.
- **Elite:** Retraces the global best route to reinforce its pheromones.

### 4. Local Search (2-opt)

To further improve solution quality, a modified **2-opt Local Search** is applied to the best ant in each iteration. It attempts to swap nodes in the route to see if a shorter total time can be achieved.



## 🚀 Usage

1. In `ThemePark.py`, specify your target theme park name and the attractions you want to visit. The script will automatically:
   - Scrape average queue times by hour (all-time data) from [queue-times.com](https://queue-times.com/)
   - Fetch OSM (OpenStreetMap) data for the attractions
   - Request walking times between attractions from OSRM based on the OSM data

2. Run `ACO_for_TDTSP.py` to solve the optimization problem. You'll receive:
   - A recommended visiting order for your selected attractions
   - The estimated total time required (walking + waiting + playing)



### 🎯 Exploring Different Scenarios

One of the most fascinating aspects of this tool is seeing how the optimal route adapts to different parameters. Experiment with various inputs and observe how the recommended visiting order and estimated total time change:

- **Try different departure times:** Compare routes starting at 9:00 AM vs. 11:00 AM. You'll often discover that entering the park early can dramatically reduce total wait times, as the algorithm can schedule popular attractions during their typically quieter morning hours.

- **Try different starting locations:** Change your departure point and see how the optimal route reorganizes itself. Different starting locations can lead to significantly different path sequences and total time estimates.

- **Try different sets of attractions:** Modify your list of target attractions and observe how the algorithm adapts. Adding or removing attractions will reveal how the optimization balances walking distances, queue times, and overall efficiency.

By exploring these variations, you'll gain valuable insights into route planning strategies and discover the most efficient way to maximize your theme park experience.



## 🔗 Future Improvements

Future research may include using historical data and machine learning to develop more accurate wait time prediction algorithms, replacing the current linear interpolation method with more sophisticated forecasting models.
