import re
import sympy
import json
from mendeleev import get_all_elements
import datetime

mass_cache = {}
elem_cache = []

for element in get_all_elements():
    mass_cache[element.symbol] = element.mass
    elem_cache.append(element.symbol)

def extract_multiplier(block):
    multiplier = ""
    for char in block:
        if char.isdigit():
            multiplier += char
        else:
            break
    if multiplier == "":
        multiplier = 1
    else:
        multiplier = int(multiplier)
    return multiplier

def joinBlocks(block1, block2):
    """
    Join two blocks and return the result.
    """
    for element in block2:
        if element in block1:
            block1[element] += block2[element]
        else:
            block1[element] = block2[element]
    return block1

def parse_formular_block(formula):
    """
    Parse chemical formular block and return a dictionary with elements as keys and their number as values.
    No handling of parentheses is done.
    """
    elements = re.findall(r'([A-Z][a-z]*)(\d*)', formula)
    return dict((element, int(count) if count else 1) for element, count in elements)

def multiply_block(block, n):
    """
    Multiply the number of each element in the block by n.
    """
    return {element: count * n for element, count in block.items()}

def parseNextParenthesis(formula):
    """
    Parse the next parenthesis in the formula and return the formula without the parenthesis and the parenthesis content.
    """
    startc = ""
    for i in range(len(formula)):
        if formula[i] == '(':
            start = i
        if formula[i] == ')':
            end = i
            # if next char is a number, add it to startc until next char is not a number
            if end+1 < len(formula):
                while formula[end+1].isdigit():
                    startc += formula[end+1]
                    end += 1
                    if end+1 >= len(formula):
                        break
            else:
                startc += '1'
            startc = int(startc)
            #remove parentheses and number and rebuild formula
            return [formula[:start] + formula[end+1:], multiply_block(parse_formular_block(formula[start:end]), startc)]

def parse_block(formula):
    """
    Parse chemical formular block and return a dictionary with elements as keys and their number as values.
    Handling of parentheses is done.
    """
    ##first exclude parentheses from the formula
    ##also exlclude the number after the parentheses
    ##e.g. (CH3)2COOH -> CH3COOH

    #find all parentheses
    finaldata = {}
    #check if there are no nested parentheses and no wrongly placed parentheses
    closed = True
    formula = formula.replace(' ', '')
    for i in range(len(formula)):
        if formula[i] == '(':
            if not closed:
                raise ValueError("Bilanciamento invalido: parentesi annidate")
            closed = False
        if formula[i] == ')':
            if closed:
                raise ValueError("Bilanciamento invalido: le parentesi sono prive di senso")
            closed = True

    while '(' in formula:
        result = parseNextParenthesis(formula)
        formula = result[0]
        finaldata = joinBlocks(finaldata, result[1])
    #parse the rest of the formula
    finaldata = joinBlocks(finaldata, parse_formular_block(formula))
    return finaldata

def parse(balancing):
    """
    Parse the balancing.
    """
    #split balancing into blocks
    balancing = balancing.replace(' ', '')
    if not re.match(r'^[A-Za-z0-9\(\)\+\-\>\s]*$', balancing): #az AZ 09 () + ->
        raise ValueError("Bilanciamento invalido: caratteri non validi")

    sections = balancing.split('->')
    #parse each block
    if len(sections) != 2 or sections[0] == "" or sections[1] == "":
        raise ValueError("Bilanciamento invalido: la reazione non segue il formato R1 + R2 + ... -> P1 + P2 + ...")
    
    left_blocks = sections[0].split('+')
    right_blocks = sections[1].split('+')
    out = {
        "left": [parse_block(block) for block in left_blocks],
        "right": [parse_block(block) for block in right_blocks]
    }
    #check if there are no empty blocks
    for block in out["left"]:
        if block == {}:
            raise ValueError("Bilanciamento invalido: gruppo vuoto")
    for block in out["right"]:
        if block == {}:
            raise ValueError("Bilanciamento invalido: gruppo vuoto")
    #check if the blocks contain valid elements with mendeleev
    for block in out["left"]:
        for element in block:
            if not element in elem_cache:
                raise ValueError("Bilanciamento invalido: presenza di elementi non validi")
    for block in out["right"]:
        for element in block:
            if not element in elem_cache:
                raise ValueError("Bilanciamento invalido: presenza di elementi non validi")
    #check if the block contain negative atoms
    for block in out["left"]:
        for element in block:
            if block[element] < 1:
                raise ValueError("Bilanciamento invalido: presenza di atomi minori di 1")
    return out
def is_balanced(balancing):
    """
    Check if the sum of the elements in the left hand is equal to the sum of the elements in the right hand
    """
    left = balancing["left"]
    right = balancing["right"]
    left_sum = {}
    right_sum = {}
    for block in left:
        left_sum = joinBlocks(left_sum, block)
    for block in right:
        right_sum = joinBlocks(right_sum, block)
    return left_sum == right_sum


def balance_algebra_numpy(parsed):
    """
    Balance the balancing using algebra.
    Use sympy and linear algebra to solve the problem.
    Keep everything as simple as possible.
    Input: {'left': [{'C': 3, 'H': 8}, {'O': 2}], 'right': [{'C': 1, 'O': 2}, {'H': 2, 'O': 1}]}
    Output: {'left': [1, 5], 'right': [3, 4]}
    """
    try:
        if is_balanced(parsed):
            block_multipliers_left = [1 for _ in parsed["left"]]
            block_multipliers_right = [1 for _ in parsed["right"]]
            return {"left": block_multipliers_left, "right": block_multipliers_right}
        #create list of elements
        elements = []
        for block in parsed["left"]:
            for element in block:
                if element not in elements:
                    elements.append(element)
        for block in parsed["right"]:
            for element in block:
                if element not in elements:
                    elements.append(element)
        #create matrix
        matrix = []
        for block in parsed["left"]:
            row = []
            for element in elements:
                if element in block:
                    row.append(block[element])
                else:
                    row.append(0)
            matrix.append(row)
        for block in parsed["right"]:
            row = []
            for element in elements:
                if element in block:
                    row.append(-block[element])
                else:
                    row.append(0)
            matrix.append(row)
        #invert rows and columns
        invr = []
        # from 
        # [[3, 8, 0],
        #  [0, 0, 2],
        #  [1, 0, 2],
        #  [0, 2, 1]]
        # to
        # [[3, 0, 1, 0],
        #  [8, 0, 0, 2],
        #  [0, 2, 2, 1]]
        for i in range(len(elements)):
            invr.append([row[i] for row in matrix])
        matrix = invr
        A = sympy.Matrix(matrix)
        coeffs = A.nullspace()[0]
        coeffs *= sympy.lcm([term.q for term in coeffs])
        coeffs = [int(term) for term in coeffs]
        #split in lefthand and righthand
        block_multipliers_left = coeffs[:len(parsed["left"])]
        block_multipliers_right = coeffs[len(parsed["left"]):]
        for multiplier in block_multipliers_left:
            if multiplier < 1:
                raise ValueError("Bilanciamento impossibile")
        for multiplier in block_multipliers_right:
            if multiplier < 1:
                raise ValueError("Bilanciamento impossibile")
        return {"left": block_multipliers_left, "right": block_multipliers_right}
    except:
        raise ValueError("Bilanciamento impossibile")
def balance_and_rebuild(balancing, log=[]):
    """
    Balance the reaction and turn it into a printable string.
    """
    time = datetime.datetime.now()
    parsed = parse(balancing)
    log.append("Ho controllato che la reazione sia valida.\n")
    log.append("Ho convertito la reazione in un formato leggibile per il computer:\n")
    log.append("```json\n"+json.dumps(parsed)+"\n```")
    log.append("\n")
    balanced = balance_algebra_numpy(parsed)
    log.append("Ho bilanciato la reazione utilizzado l'algebra lineare, ottenendo i seguenti moltiplicatori: (")
    for i in range(len(balanced["left"])):
        log.append(str(balanced["left"][i]))
        if i != len(balanced["left"])-1:
            log.append(", ")
    log.append(") -> (")
    for i in range(len(balanced["right"])):
        log.append(str(balanced["right"][i]))
        if i != len(balanced["right"])-1:
            log.append(", ")
    log.append(")\n")
    stripped = balancing.replace(' ', '')
    sections = stripped.split('->')
    left_blocks = sections[0].split('+')
    right_blocks = sections[1].split('+')
    #rebuild putting multiplier in front of each block
    left = []
    right = []
    removedD = False
    for i in range(len(left_blocks)):
        #drop first digit of block if it's there
        while left_blocks[i][0].isdigit():
            removedD = True
            left_blocks[i] = left_blocks[i][1:]
        if balanced["left"][i] != 1:
            left.append(str(balanced["left"][i]) + left_blocks[i])
        else:
            left.append(left_blocks[i])
    for i in range(len(right_blocks)):
        #drop first digit of jblock if it's there
        while right_blocks[i][0].isdigit():
            removedD = True
            right_blocks[i] = right_blocks[i][1:]
        if balanced["right"][i] != 1:
            right.append(str(balanced["right"][i]) + right_blocks[i])
        else:
            right.append(right_blocks[i])
    if removedD:
        log.append("Ho rimosso i moltiplicatori dai blocchi.\n")
    log.append("Ho ricostruito la reazione immettendo i moltiplicatori all'inizio di ogni blocco.\n")
    log.append("Tempo di computazione: " + str((datetime.datetime.now() - time).total_seconds()))
    return " + ".join(left) + " -> " + " + ".join(right)

def extractMultipliers(balanced):
    parsed = parse(balanced)
    balancing = balanced.replace(' ', '')
    sections = balancing.split('->')
    left_blocks = sections[0].split('+')
    right_blocks = sections[1].split('+')
    left_multipliers = []
    right_multipliers = []
    for i in left_blocks:
        left_multipliers.append(extract_multiplier(i))
    for i in right_blocks:
        right_multipliers.append(extract_multiplier(i))
    return {"left": left_multipliers, "right": right_multipliers}

def balance_molar(balanced, index, afterArrow, amount):
    parsed = parse(balanced)
    left_blocks = parsed["left"]
    right_blocks = parsed["right"]
    index = int(index)
    amount = float(amount)
    afterArrow = bool(afterArrow)
    if index < 0:
        raise ValueError("L'indice non può essere negativo.")
    if amount < 0:
        raise ValueError("La quantità non può essere negativa.")
    extractedMultipliers = extractMultipliers(balanced)
    left_multipliers = extractedMultipliers["left"]
    right_multipliers = extractedMultipliers["right"]
    multiplier = 1
    if afterArrow:
        multiplier = right_multipliers[index]
    else:
        multiplier = left_multipliers[index]
    
    realAmount = amount / multiplier
    for i in range(len(left_multipliers)):
        left_multipliers[i] *= realAmount
    for i in range(len(right_multipliers)):
        right_multipliers[i] *= realAmount
    #convert to int if not a decimal
    for i in range(len(left_multipliers)):
        left_multipliers[i] = rou3(left_multipliers[i])
    for i in range(len(right_multipliers)):
        right_multipliers[i] = rou3(right_multipliers[i])
    left_masses = []
    right_masses = []
    for i in range(len(left_multipliers)):
        left_masses.append(rou3(left_multipliers[i] * get_block_mass(left_blocks[i])))
    for i in range(len(right_multipliers)):
        right_masses.append(rou3(right_multipliers[i] * get_block_mass(right_blocks[i])))
    return {
        "masses": {
            "left": left_masses,
            "right": right_masses
        },
        "molar": {
            "left": left_multipliers,
            "right": right_multipliers
        }
    }

def get_block_mass(block):
    """
    Get the mass of a block.
    Block is already in format {element: coefficient}
    Use mendeleev to get the mass of each element.
    """
    mass = 0
    for element in block:
        mass += block[element] * mass_cache[element]
    return mass
    
def rou3(number):
    number = round(number, 3)
    if number % 1 == 0:
        return int(number)
    return number

def balance_mass(balanced, index, afterArrow, mass):
    parsed = parse((balanced))
    index = int(index)
    afterArrow = bool(afterArrow)
    mass = float(mass)
    
    afterArrow = bool(afterArrow)
    molar_config = balance_molar(balanced, index, afterArrow, 1)["molar"]
    left_masses = []
    right_masses = [] 
    """
    We have to find the mass of the block provided. We'll use get_block_mass to do that.
    Then, we have to find the multiplier that will make the mass of the block provided equal to the mass provided.
    That is the new molar config for the block provided. We have to change every other block's molar config to keep the reaction proportional.
    """
    if afterArrow:
        block = parsed["right"][index]
    else:
        block = parsed["left"][index]
    block_mass = get_block_mass(block)
    multiplier = mass / block_mass
    for i in range(len(molar_config["left"])):
        molar_config["left"][i] *= multiplier
        molar_config["left"][i] = (molar_config["left"][i])
        left_masses.append((get_block_mass(parsed["left"][i])*molar_config["left"][i]))
    for i in range(len(molar_config["right"])):
        molar_config["right"][i] *= multiplier
        molar_config["right"][i] = (molar_config["right"][i])
        right_masses.append((get_block_mass(parsed["right"][i])*molar_config["right"][i]))
    
    return {
        "masses": {
            "left": left_masses,
            "right": right_masses
        },
        "molar": molar_config
    }
