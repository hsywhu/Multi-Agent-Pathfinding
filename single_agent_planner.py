import heapq


def move(loc, dir):
    directions = [(0, -1), (1, 0), (0, 1), (-1, 0), (0, 0)]
    return loc[0] + directions[dir][0], loc[1] + directions[dir][1]


def get_sum_of_cost(paths):
    rst = 0
    for path in paths:
        rst += len(path) - 1
    return rst


def compute_heuristics(my_map, goal):
    # Use Dijkstra to build a shortest-path tree rooted at the goal location
    open_list = []
    closed_list = dict()
    root = {'loc': goal, 'cost': 0}
    heapq.heappush(open_list, (root['cost'], goal, root))
    closed_list[goal] = root
    while len(open_list) > 0:
        (cost, loc, curr) = heapq.heappop(open_list)
        for dir in range(4):
            child_loc = move(loc, dir)
            child_cost = cost + 1
            if child_loc[0] < 0 or child_loc[0] >= len(my_map) \
               or child_loc[1] < 0 or child_loc[1] >= len(my_map[0]):
               continue
            if my_map[child_loc[0]][child_loc[1]]:
                continue
            child = {'loc': child_loc, 'cost': child_cost}
            if child_loc in closed_list:
                existing_node = closed_list[child_loc]
                if existing_node['cost'] > child_cost:
                    closed_list[child_loc] = child
                    # open_list.delete((existing_node['cost'], existing_node['loc'], existing_node))
                    heapq.heappush(open_list, (child_cost, child_loc, child))
            else:
                closed_list[child_loc] = child
                heapq.heappush(open_list, (child_cost, child_loc, child))

    # build the heuristics table
    h_values = dict()
    for loc, node in closed_list.items():
        h_values[loc] = node['cost']
    return h_values


def build_constraint_table(constraints, agent):
    ##############################
    # Task 1.2/1.3: Return a table that constains the list of constraints of
    #               the given agent for each time step. The table can be used
    #               for a more efficient constraint violation check in the
    #               is_constrained function.

    # find the biggest timestep first
    biggest_timestep = -1
    for constraint in constraints:
        if constraint['timestep'] > biggest_timestep:
            biggest_timestep = constraint['timestep']

    # init the constraint table with the length of biggest timestep
    constraint_table = []
    for _ in range(biggest_timestep + 1):
        constraint_table.append([])

    # fill in the constraint table
    for constraint in constraints:
        if constraint['positive']:
            if len(constraint['loc']) == 1:
                # process as positive vertex constraint
                if constraint['agent'] == agent:
                    constraint_table[constraint['timestep']].append({'loc': constraint['loc'], 'positive': True})
                else:
                    constraint_table[constraint['timestep']].append({'loc': constraint['loc'], 'positive': False})
            else:
                # process as positive edge constraint
                if constraint['agent'] == agent:
                    constraint_table[constraint['timestep']].append({'loc': constraint['loc'], 'positive': True})
                else:
                    constraint_table[constraint['timestep']].append({'loc': constraint['loc'], 'positive': False})
        else:   # negative constraint
            if constraint['agent'] == agent:
                constraint_table[constraint['timestep']].append({'loc': constraint['loc'], 'positive': False})
            # else:
            #     constraint_table[constraint['timestep']].append({'loc': constraint['loc'], 'positvie': False})
    return constraint_table


def get_location(path, time):
    if time < 0:
        return path[0]
    elif time < len(path):
        return path[time]
    else:
        return path[-1]  # wait at the goal location


def get_path(goal_node):
    path = []
    curr = goal_node
    while curr is not None:
        path.append(curr['loc'])
        curr = curr['parent']
    path.reverse()
    return path


def is_constrained(curr_loc, next_loc, next_time, constraint_table):
    ##############################
    # Task 1.2/1.3: Check if a move from curr_loc to next_loc at time step next_time violates
    #               any given constraint. For efficiency the constraints are indexed in a constraint_table
    #               by time step, see build_constraint_table.

    # check if next_time is within the max timestep of constraint_table
    # if next_time > len(constraint_table) - 1:
    #     return False

    # Task 2.3 Adding Additional Constraints
    # adds additional constraints that apply not only to the time step when agents reach their goal locations but
    # also to all future time steps
    if len(constraint_table) == 0:
        return False
    next_time = min(next_time, len(constraint_table) - 1)

    for constraint in constraint_table[next_time]:
        # process positive constraint first
        if constraint['positive'] and constraint['loc'][0] == next_loc:
            return True
        elif not constraint['positive']:    # negative constraint
            # handle vertex constraint
            if len(constraint['loc']) == 1 and constraint['loc'][0] == next_loc:
                return True
            # handle edge constraint
            elif len(constraint['loc']) == 2 and constraint['loc'][0] == curr_loc and constraint['loc'][1] == next_loc:
                return True
    return False


def push_node(open_list, node):
    heapq.heappush(open_list, (node['g_val'] + node['h_val'], node['h_val'], node['loc'], node))


def pop_node(open_list):
    _, _, _, curr = heapq.heappop(open_list)
    return curr


def compare_nodes(n1, n2):
    """Return true is n1 is better than n2."""
    return n1['g_val'] + n1['h_val'] < n2['g_val'] + n2['h_val']


def a_star(my_map, start_loc, goal_loc, h_values, agent, constraints):
    """ my_map      - binary obstacle map
        start_loc   - start position
        goal_loc    - goal position
        agent       - the agent that is being re-planned
        constraints - constraints defining where robot should or cannot go at each timestep
    """

    ##############################
    # Task 1.1: Extend the A* search to search in the space-time domain
    #           rather than space domain, only.

    constraint_table = build_constraint_table(constraints, agent)
    open_list = []
    closed_list = dict()

    # Task 2.4: Set an upper bound on the path length
    timestep_upper_bound = len(my_map[0]) * len(my_map[1]) * 3

    # calculate earliest goal timestep from the constraint table
    earliest_goal_timestep = 0
    for i in range(len(constraint_table) - 1, -1, -1):
        if is_constrained(goal_loc, goal_loc, i, constraint_table):
            earliest_goal_timestep = i + 1
            break

    h_value = h_values[start_loc]
    root = {'loc': start_loc, 'g_val': 0, 'h_val': h_value, 'parent': None, 'timestep': 0}
    push_node(open_list, root)
    closed_list[(root['loc'], root['timestep'])] = root
    while len(open_list) > 0:
        curr = pop_node(open_list)

        # Task 2.4: check if the current move has exceeded the upper bould
        if curr['timestep'] > timestep_upper_bound:
            print('Timestep exceeded the upper bound')
            return None

        #############################
        # Task 1.4: Adjust the goal test condition to handle goal constraints
        if curr['loc'] == goal_loc and curr['timestep'] >= earliest_goal_timestep:
            return get_path(curr)
        for dir in range(5):
            child_loc = move(curr['loc'], dir)
            # check if the new loc is within the map
            if child_loc[0] < 0 or child_loc[1] < 0 or child_loc[0] >= len(my_map) or child_loc[1] >= len(my_map[0]):
                continue
            # check if the new loc on the map is available
            if my_map[child_loc[0]][child_loc[1]]:
                continue
            # check if the new loc satisfies the constraints
            if is_constrained(curr['loc'], child_loc, curr['timestep'] + 1, constraint_table):
                continue
            child = {'loc': child_loc,
                     'g_val': curr['g_val'] + 1,
                     'h_val': h_values[child_loc],
                     'parent': curr,
                     'timestep': curr['timestep'] + 1}
            if (child['loc'], child['timestep']) in closed_list:
                existing_node = closed_list[(child['loc'], child['timestep'])]
                if compare_nodes(child, existing_node):
                    closed_list[(child['loc'], child['timestep'])] = child
                    push_node(open_list, child)
            else:
                closed_list[(child['loc'], child['timestep'])] = child
                push_node(open_list, child)

    return None  # Failed to find solutions
