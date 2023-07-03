import datetime
import os
import sys
import numpy as np
import pandas as pd
from scipy.optimize import newton

pd.set_option('display.max_columns', None)
pd.options.display.float_format = '{:,.5f}'.format
# Get the path to the desktop
desktop_path = os.path.join(os.path.join(os.environ['USERPROFILE']), 'Desktop')

# Get user's date of birth
while True:
    dob_str = input("\n\nEnter your date of birth (YYYY-MM-DD): ")
    try:
        dob = datetime.datetime.strptime(dob_str, '%Y-%m-%d')
        break
    except ValueError:
        print("Invalid date format. Please enter date in YYYY-MM-DD format.")

# Calculate age
today = datetime.date.today()
age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))

print("AGE:", age)

if age < 20 or age > 40:
    print("This policy may not be suited for your age.")
    sys.exit()

# summ assured, assumptions
sum_assured_str = input("\n\nPlease enter the sum assured value: ")
sum_assured = int(sum_assured_str.replace(",", ""))
# assume premium
assumed_prem_str = input("\n\nPlease enter an assumed premium value above 500000: ")
assumed_prem = int(assumed_prem_str.replace(",", ""))

# fixed assumptions
risk_rate = float(0.13)
unit_interest = float(0.15)
non_unit_interest = float(0.1485)
bo_spread = float(0.03)
alloc_1 = float(0.6)
alloc_yr = float(0.98)
inflation_rate = float(0.09)
mgt_charge = float(0.01)

# Percentages for expenses
In_value = float(0.0175)
Ren_value = float(0.00015)
In_Exp = In_value * sum_assured
Ren_Exp = Ren_value * sum_assured

# Percentages for commissions
In_valueC = float(0.29)
Ren_valueC = float(0.03)
In_Com = In_valueC * assumed_prem
Ren_Com = Ren_valueC * assumed_prem

# Get term range
while True:
    term_range = input("\n\nDesired term (range between 3 and 10): ")
    try:
        term_range = int(term_range)
        if term_range < 3 or term_range > 10:
            raise ValueError
        break
    except ValueError:
        print("Invalid term range. Please enter a number between 3 and 10.")

# Get user's gender
while True:
    gender = input("\n\nEnter your gender (Male or Female): ")
    if gender.lower() not in ['male', 'female']:
        print("Invalid gender. Please enter either Male or Female.")
    else:
        break

# Construct the full path to the file
file_name = f'Mortality_{gender}.xlsx'
file_path = os.path.join(desktop_path, file_name)

# Read the file into a DataFrame
mortality_data = pd.read_excel(file_path)

# Construct table with death rates, surrender rates, dependent death rates, dependent surrender rates, survival rates and based survival rates
start_age = age
end_age = age + term_range

table_data = {'Age': [], 'Death rate': [], 'Surrender rate': [], 'Dep.death.rates': [], 'Dep.Surr.rate': [],
              'Surviv.rate': [], 'Based.Survival': []}
based_survival = 1

for i in range(start_age, end_age):
    if i in mortality_data['Age'].values:
        death_rate = mortality_data.loc[mortality_data['Age'] == i, 'Death rate'].values[0]
        table_data['Age'].append(i)
        table_data['Death rate'].append(death_rate)
        table_data['Dep.death.rates'].append(death_rate)

        if i == start_age or i == end_age - 1:
            surrender_rate = 0
            table_data['Surrender rate'].append(surrender_rate)
            table_data['Dep.Surr.rate'].append(surrender_rate)
            surviv_rate = 1 - (death_rate + surrender_rate)
            table_data['Surviv.rate'].append(surviv_rate)
            table_data['Based.Survival'].append(based_survival)
            based_survival *= surviv_rate

        else:
            surrender_rate = 0.05
            table_data['Surrender rate'].append(surrender_rate)
            dep_surr_rate = surrender_rate * (1 - death_rate)
            table_data['Dep.Surr.rate'].append(dep_surr_rate)
            surviv_rate = 1 - (death_rate + dep_surr_rate)
            table_data['Surviv.rate'].append(surviv_rate)
            table_data['Based.Survival'].append(based_survival)
            based_survival *= surviv_rate

table = pd.DataFrame(data=table_data)
if not table.empty:
    table['Year'] = table['Age'] - age + 1
#   print(table)     has been commented out

#  Table for death benefits

start_age = age
end_age = age + term_range

table_benefits = {'Year': [], 'Exp.DeathB': [], 'Discount Factor': [], 'PV.DeathB': [], 'Exp.Surr': [], 'PV.Surr': [],
                  'PV.Benefit': []}

year = 1
for i in range(start_age, end_age):
    if i in mortality_data['Age'].values:
        death_rate = mortality_data.loc[mortality_data['Age'] == i, 'Death rate'].values[0]
        table_benefits['Year'].append(year)
        death_benefit = sum_assured * death_rate
        table_benefits['Exp.DeathB'].append(death_benefit)
        discount_factor = 1 / ((1 + risk_rate) ** year)
        table_benefits['Discount Factor'].append(discount_factor)
        pv_death_benefit = discount_factor * death_benefit
        table_benefits['PV.DeathB'].append(pv_death_benefit)
        dep_surr_rate = table.loc[table['Age'] == i, 'Dep.Surr.rate'].values[0]
        exp_surr = sum_assured * dep_surr_rate
        table_benefits['Exp.Surr'].append(exp_surr)
        pv_surr = exp_surr * discount_factor
        table_benefits['PV.Surr'].append(pv_surr)
        pv_benefit = pv_death_benefit + pv_surr
        table_benefits['PV.Benefit'].append(pv_benefit)
        year += 1

last_surviv_rate = table.iloc[-1]['Surviv.rate']
death_benefit = sum_assured * last_surviv_rate
table_benefits['Year'].append(year - 1)
table_benefits['Exp.DeathB'].append(death_benefit)
discount_factor = 1 / ((1 + risk_rate) ** (year - 1))
table_benefits['Discount Factor'].append(discount_factor)
pv_death_benefit = discount_factor * death_benefit
table_benefits['PV.DeathB'].append(pv_death_benefit)
table_benefits['Exp.Surr'].append(0)
pv_surr = 0
table_benefits['PV.Surr'].append(pv_surr)
pv_benefit = pv_death_benefit + pv_surr
table_benefits['PV.Benefit'].append(pv_benefit)

table2 = pd.DataFrame(data=table_benefits)
if not table2.empty:
#  print(table2)
    total_benefits = table2['PV.Benefit'].sum()
# print(f'Total Benefits: {total_benefits}') has been commented out for menu

# expenses
table_expense = table2[['Year']].copy()
table_expense.drop(table_expense.tail(1).index, inplace=True)
table_expense = table_expense.merge(table[['Year', 'Based.Survival']], on='Year')
table_expense['Discount factorE'] = 1 / ((1 + risk_rate) ** (table_expense['Year'] - 1))
table_expense['Expense'] = table_expense['Based.Survival'] * np.where(table_expense.index == 0, In_Exp, Ren_Exp)
table_expense['PV.Expense'] = table_expense['Discount factorE'] * table_expense['Expense']
table_expense['Commission'] = table_expense['Based.Survival'] * np.where(table_expense.index == 0, In_Com, Ren_Com)
table_expense['PV.Comm'] = table_expense['Commission'] * table_expense['Discount factorE']
table_expense['PV.ExpenCom'] = table_expense['PV.Expense'] + table_expense['PV.Comm']
# print(table_expense)
total_expenses = table_expense['PV.ExpenCom'].sum()
# print(f'Total Expenses and Commissions: {total_expenses}') has been commented out to the menu

Total_E_B = total_expenses + total_benefits

# premiums
table_premiums = table_expense[['Year', 'Discount factorE']].copy()
table_premiums['Prem'] = assumed_prem
table_premiums['Based.Survival'] = table['Based.Survival']
table_premiums['Exp.Prem'] = table_premiums['Prem'] * table_premiums['Based.Survival']
table_premiums['PV.Prem'] = table_premiums['Exp.Prem'] * table_premiums['Discount factorE']
# print(table_premiums)


Total_P = table_premiums['PV.Prem'].sum()
# print(f'Total Premiums are: {Total_P}')

# print(f'Total Expected Outgo is: {Total_E_B}\n')
# print(f'Total Expected Income is: {Total_P}\n')


def goal_seek(assumed_prem):
    # Recalculate commissions
    In_Com = In_valueC * assumed_prem
    Ren_Com = Ren_valueC * assumed_prem
    table_expense['Commission'] = table_expense['Based.Survival'] * np.where(table_expense.index == 0, In_Com, Ren_Com)
    table_expense['PV.Comm'] = table_expense['Commission'] * table_expense['Discount factorE']
    table_expense['PV.ExpenCom'] = table_expense['PV.Expense'] + table_expense['PV.Comm']
    total_expenses = table_expense['PV.ExpenCom'].sum()

    # Recalculate premiums
    table_premiums['Prem'] = [assumed_prem] * len(table_premiums)
    table_premiums['Based.Survival'] = table['Based.Survival']
    table_premiums['Exp.Prem'] = table_premiums['Prem'] * table_premiums['Based.Survival']
    table_premiums['PV.Prem'] = table_premiums['Exp.Prem'] * table_premiums['Discount factorE']
    Total_P = table_premiums['PV.Prem'].sum()

    # Recalculate Equation of Value
    Total_E_B = total_expenses + total_benefits
    Equation_of_Value = Total_P - Total_E_B

    return Equation_of_Value

GOAL_premium = newton(goal_seek, 0)

Equation_of_Value = goal_seek(GOAL_premium)

# print("\n")
# print(f'The Equation of value is balanced at : {Equation_of_Value}')
# print("\n")
# print(f'The Premium is : {int(GOAL_premium)}\n')

# THE UNIT FUND
# print("************THE UNIT FUND************\n")
Unit_Fund = pd.DataFrame()
Unit_Fund['Year'] = table['Year']
Unit_Fund['Premium'] = GOAL_premium
Unit_Fund['PremAllocated'] = Unit_Fund['Premium'] * np.where(Unit_Fund.index == 0, alloc_1, alloc_yr)
Unit_Fund['Bid/Offer Spread'] = bo_spread * Unit_Fund['PremAllocated']
Unit_Fund['Cost of Allocation'] = Unit_Fund['PremAllocated'] - Unit_Fund['Bid/Offer Spread']
fund_end = 0
for i in range(len(Unit_Fund)):
    if i == 0:
        Unit_Fund.loc[i, 'FundAfterAlloc'] = Unit_Fund.loc[i, 'Cost of Allocation'] + fund_end
    else:
        Unit_Fund.loc[i, 'FundAfterAlloc'] = Unit_Fund.loc[i, 'Cost of Allocation'] + Unit_Fund.loc[i-1, 'FundyearEnd']
    Unit_Fund.loc[i, 'FundUncharged'] = Unit_Fund.loc[i, 'FundAfterAlloc'] * (1 + unit_interest)
    Unit_Fund.loc[i, 'MgtCharge'] = mgt_charge * Unit_Fund.loc[i, 'FundUncharged']
    Unit_Fund.loc[i, 'FundyearEnd'] = Unit_Fund.loc[i, 'FundUncharged'] - Unit_Fund.loc[i, 'MgtCharge']
# print(Unit_Fund)

In_ComP = In_valueC * GOAL_premium
Ren_ComP = Ren_valueC * GOAL_premium

# THE NON UNIT FUND
# print("\n************THE NON-UNIT FUND************\n")
Non_Unit = pd.DataFrame()
Non_Unit['Year'] = Unit_Fund['Year']
Non_Unit = Non_Unit.merge(Unit_Fund[['Year', 'Premium', 'Cost of Allocation']], on='Year')
Non_Unit['PremiumLessCA'] = Non_Unit['Premium'] - Non_Unit['Cost of Allocation']
Non_Unit['Expenses'] = np.where(Non_Unit.index == 0, In_Exp, Ren_Exp * ((1 + inflation_rate) ** Non_Unit['Year']))
Non_Unit['Commission'] = np.where(Non_Unit.index == 0, In_ComP, Ren_ComP)
Non_Unit['Interest'] = (Non_Unit['PremiumLessCA'] - (Non_Unit['Expenses'] + Non_Unit['Commission'])) * non_unit_interest
Non_Unit['ExtraDeathCost'] = np.where(Non_Unit.index == len(Non_Unit) - 1, 0, np.where(Unit_Fund['FundyearEnd'] < sum_assured, (sum_assured - Unit_Fund['FundyearEnd']) * table['Dep.death.rates'], 0))
Non_Unit['Maturity cost'] = 0
Non_Unit.loc[len(Non_Unit) - 1, 'Maturity cost'] = np.where(Unit_Fund.loc[len(Unit_Fund) - 1, 'FundyearEnd'] < sum_assured, (sum_assured - Unit_Fund.loc[len(Unit_Fund) - 1, 'FundyearEnd'])*table.loc[len(table)-1, 'Surviv.rate'], 0)
Non_Unit['MgtCharge'] = Unit_Fund['MgtCharge']
Non_Unit['Profit Vector'] = Non_Unit['PremiumLessCA'] - Non_Unit['Expenses'] - Non_Unit['Commission'] + Non_Unit['Interest'] - Non_Unit['ExtraDeathCost'] - Non_Unit['Maturity cost'] + Non_Unit['MgtCharge']
# print(Non_Unit)

# NET PRESENT VALUE OF PROFITS
# print("\n************NPV of Profits************\n")

NPV_PROFIT = pd.DataFrame()
NPV_PROFIT['Year'] = Non_Unit['Year']
NPV_PROFIT = NPV_PROFIT.merge(Non_Unit[['Year', 'Profit Vector']], on='Year')
NPV_PROFIT['Discount factor'] = 1 / ((1 + risk_rate) ** NPV_PROFIT['Year'])
NPV_PROFIT = NPV_PROFIT.merge(table[['Year', 'Based.Survival']], on='Year')
NPV_PROFIT['DiscountedProfit'] = NPV_PROFIT['Profit Vector'] * NPV_PROFIT['Discount factor'] * NPV_PROFIT['Based.Survival']
# print(NPV_PROFIT)

NetPV_Profits = NPV_PROFIT['DiscountedProfit'].sum()
# print("\n**********************\n")
# print(f'The Net Present Value of Profits is : {int(NetPV_Profits)}\n')


# NET PRESENT VALUE OF PREMIUM2003
# print("\n************NPV of Premiums************\n")

NPV_PREMIUM = pd.DataFrame()
NPV_PREMIUM['Year'] = Unit_Fund['Year']
NPV_PREMIUM = NPV_PREMIUM.merge(Unit_Fund[['Year', 'Premium']], on='Year')
NPV_PREMIUM['Discount factor'] = 1 / ((1 + risk_rate) ** (NPV_PREMIUM['Year']-1))
NPV_PREMIUM = NPV_PREMIUM.merge(table[['Year', 'Based.Survival']], on='Year')
NPV_PREMIUM['DiscountedPremium'] = NPV_PREMIUM['Premium'] * NPV_PREMIUM['Discount factor'] * NPV_PREMIUM['Based.Survival']
# print(NPV_PREMIUM)

NetPV_Premiums = NPV_PREMIUM['DiscountedPremium'].sum()
# print("\n**********************\n")
# print(f'The Net Present Value of Premiums is : {int(NetPV_Premiums)}\n')

Profit_Margin = float(NetPV_Profits/NetPV_Premiums)
# print(f'\nThe Profit Margin for this product is : {Profit_Margin*100:.2f}%\n')

while True:
    print("\n\nWELCOME! Please Select from the options displayed below to proceed:\n\n")
    print("1.  Multiple Decrements Table")
    print("2.  Pricing Model")
    print("3.  Profit Testing Model")
    print("4.  Display only Premium ")
    print("5.  Display only Profit Margin")
    print("6. Terminate the program")

    choice = input("\nPlease Select an Option to display what you would like to see: ")

    if choice == "1":
        # This prints the Table of Multiple decrements that has been computed
        print("\n")
        print("\n*************************************** Multiple decrements ************************************\n\n")
        print(table.to_string(index=False))
        print("\n")
        print("\n")

    elif choice == "2":
        # This prints out the table that calculates Expected Benefits for equation of value
        print("\n")
        print("\n")
        print("\n*************************************** Pricing Model ****************************************\n\n")
        print(table2.to_string(index=False))
        print(f'\n\nTotal Expected Benefits are : {total_benefits}\n')
        print("\n")
        # This prints out the table that calculates Expected expenses for equation of value
        print("\n")
        print(table_expense.to_string(index=False))
        print(f'\n\nTotal Expenses and Commissions: {total_expenses}\n')
        print("\n")
        print(table_premiums.to_string(index=False))
        print(f'\n\nTotal Premiums are: {Total_P}\n')
        print("\n")
        print(f'\nTotal Expected Outgo is: {Total_E_B}\n')
        print(f'\nTotal Expected Income is: {Total_P}\n')
        print("\nAfter setting Equation of value to zero\n")
        print(f'The Equation of value is balanced at : {int(Equation_of_Value)}')
        print("\n")
        print(f'The Premium is : {int(GOAL_premium)}\n')
        print("\n")
        print("\n")

    elif choice == "3":
        # This displays the profit test model
        print("\n")
        print("\n\n*****************************************THE UNIT FUND*****************************************\n\n")
        print(Unit_Fund.to_string(index=False))
        print("\n\n***************************************THE NON-UNIT FUND***************************************\n\n")
        print(Non_Unit.to_string(index=False))
        print("\n\n*****************************************NPV of Profits***************************************\n\n")
        print(NPV_PROFIT.to_string(index=False))
        print("\n**********************\n\n")
        print(f'The Net Present Value of Profits is : {int(NetPV_Profits)}\n')
        print("\n\n*****************************************NPV of Premiums***************************************\n\n")
        print(NPV_PREMIUM.to_string(index=False))
        print("\n**********************\n\n")
        print(f'The Net Present Value of Premiums is : {int(NetPV_Premiums)}\n')
        # This displays the profitability
        print("\n")
        print(f'\n\nThe Profit Margin for this product is : {Profit_Margin * 100:.2f}%\n\n\n')
        print("\n")

    elif choice == "4":
        # Do something for option 4
        print("\n")
        print("\n")
        print(f'The Premium is : {int(GOAL_premium)}\n')
        print("\n")

    elif choice == "5":
        # This displays the profitability
        print("\n")
        print(f'\n\nThe Profit Margin for this product is : {Profit_Margin * 100:.2f}%\n\n\n')
        print("\n")

    elif choice == "6":
        print("\n\nExiting Program..............\n")
        break
    else:
        print("\n")
        print("The option selected does not exist in this program. Please try again with either 1,2,3,4,5,6,7,8,9,10 or 11.")
        print("\n")

