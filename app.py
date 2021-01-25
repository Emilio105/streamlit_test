import streamlit as st
import pandas as pd
import altair as alt
from gekko import GEKKO
import math
st.set_page_config(layout="wide")
st.header("API Pricing Royalties Calculator")

st.subheader("Pricing Information:")

info = [
 {
   "Platform": "Here",
   "Average Pricing (USD)": 1,
   "Requests": 1000,
   "Other Information": "$450 + 1 Euro per 1000 after 1Mil Calls"
 },
 {
   "Platform": "Google",
   "Average Pricing (USD)": 5,
   "Requests": 1000,
   "Other Information": "Premium Pricing Available"
 },
 {
   "Platform": "Tom Tom",
   "Average Pricing (USD)": 0.45,
   "Requests": 1000,
   "Other Information": "*No transport -> Just directions"
 },
 {
   "Platform": "Map Box",
   "Average Pricing (USD)": 1.6,
   "Requests": 1000,
   "Other Information": "*No transport -> Just directions"
 },
 {
   "Platform": "Navitia",
   "Average Pricing (USD)": 1.895,
   "Requests": 1000,
   "Other Information": "Owned by French Mobility Company Kisio Digital"
 },
 {
   "Platform": "Azure maps",
   "Average Pricing (USD)": 4.85,
   "Requests": 1000,
   "Other Information": "*From Moovit"
 },
 {
   "Platform": "Foursquare",
   "Average Pricing (USD)": 2,
   "Requests": 1000,
   "Other Information": "$599 Upfront"
 }
]

Info_df = pd.DataFrame(info)
Info_df.index = Info_df.Platform
Info_df = Info_df.drop(columns="Platform")


st.table(Info_df)

pricing =   {
    "Here": 1,
    "Google": 5,
    "Tom Tom": 0.45,
    "Map Box": 1.6,
    "Navitia": 1.9,
    "Azure maps": 4.85,
    "Foursquare": 2
  }

p_info = [
 {
   "Size": "Large",
   "Company Model": "Uber",
   "1k Calls Made": 780530,
   "Provider": "Google"
 },
 {
   "Size": "Medium",
   "Company Model": "Cabify",
   "1k Calls Made": 117079,
   "Provider": "Google"
 },
 {
   "Size": "Small",
   "Company Model": "Guatrain",
   "1k Calls Made": 21819,
   "Provider": "WIMT"
 }
]

p_info_df = pd.DataFrame(p_info)
p_info_df.index = p_info_df.Size
p_info_df = p_info_df.drop(columns="Size")

calls_per_company_size = {
    "l":780530,
    "m":117080,
    "s":21820
    }

sample = 5000

st.sidebar.subheader("Revenue Calculator: Select Desired Values")
Royalties = st.sidebar.slider("Royalties %", 0.1, 10.0, 1.0, 0.025) 
Upfront_Payment = st.sidebar.number_input("Upfront Cost Charged to Client $", value=0)
Desired_revenue = st.sidebar.number_input("Desired Revenue per year ($)", value=150000)
  

def find_number_of_calls(r, upfront_cost, price, revenue):
    number_of_calls = (revenue - upfront_cost)/(price*(r/100))
    return number_of_calls

def get_pricing_values(price_dict, revenue, upfront_cost, r):
    # entries = []
    entries = {}
    
    for i in price_dict.keys():
        calls = find_number_of_calls(r=r, upfront_cost=upfront_cost, revenue=revenue, price = price_dict[i])
        entries[i] = round(calls)
        # entries.append({"Provider": "{0}".format(i), "1k Calls Required" : round(calls)})
    return pd.Series(entries, name = "1k Calls")


def calculate_client_revenue(prices, company_calls, small, med, large, r):
    ent = []
    
    for i in prices.keys():
        
        if i == "Here":
            s_revenue = prices[i]*r*((company_calls['s']-1000)*small)
            m_revenue = prices[i]*r*((company_calls['m']-1000)*med)
            l_revenue = prices[i]*r*((company_calls['l']-100)*large)            
            
        else:        
            s_revenue = prices[i]*r*(company_calls['s']*small)
            m_revenue = prices[i]*r*(company_calls['m']*med)
            l_revenue = prices[i]*r*(company_calls['l']*large)

        ent.append(dict(
            revenue = s_revenue,
            client_size = "Small",
            provider = i))

        ent.append(dict(
            revenue = m_revenue,
            client_size = "Medium",
            provider = i))

        ent.append(dict(
            revenue = l_revenue,
            client_size = "Large",
            provider = i))
        
    return pd.DataFrame(ent)


def get_optimal_client_numbers(price, r, calls, desired_revenue):
    m = GEKKO()
    rev_opt = m.Param(desired_revenue)
    c_s, c_m =  [m.Var(lb=0, integer=True) for i in range(2)]
    c_l = m.Var(lb=0, integer=True)

    m.Equation((c_s*calls['s'] + c_m*calls['m'] + c_l*calls['l'])*price*r == rev_opt)
    m.Obj(0.115*c_s + 0.75*c_m + 4*c_l)
    m.options.IMODE = 3
    m.solve(disp=False)
    
    return math.ceil(c_s.value[0]), math.ceil(c_m.value[0]), math.ceil(c_l.value[0])
#     return c_s.value[0] , c_m.value[0], c_l.value[0]
    
@st.cache  
def calculate_client_numbers(prices, company_calls, desired_revenue, r):
    ent = []
    
    for i in prices.keys():
        
        small, med, large = get_optimal_client_numbers(prices[i], r, company_calls, desired_revenue)
        
        if i == "Here":
            s_revenue = prices[i]*r*((company_calls['s']-1000)*small)
            m_revenue = prices[i]*r*((company_calls['m']-1000)*med)
            l_revenue = prices[i]*r*((company_calls['l']-100)*large)            
            
        else:        
            s_revenue = prices[i]*r*(company_calls['s']*small)
            m_revenue = prices[i]*r*(company_calls['m']*med)
            l_revenue = prices[i]*r*(company_calls['l']*large)

        ent.append(dict(
            revenue = s_revenue,
            client_size = "Small",
            provider = i,
            clients = small))

        ent.append(dict(
            revenue = m_revenue,
            client_size = "Medium",
            provider = i,
            clients = med))

        ent.append(dict(
            revenue = l_revenue,
            client_size = "Large",
            provider = i,
            clients = large))
        
    return pd.DataFrame(ent)          

st.subheader("""Calls Required to reach desired revenue with royalties of {0}% with an upfront cost of ${1} """.format(Royalties, Upfront_Payment))

col2_, col3_, col4_, col5_  = st.beta_columns(4)
# with col1_:
#     st.write("Average Prices per 1k calls")
#     st.write(pd.Series(pricing, name="Pricing (USD)"))
with col2_:
    st.write("Calls required to reach $25k per year")
    st.write(get_pricing_values(price_dict=pricing, revenue=25000, upfront_cost=Upfront_Payment, r=Royalties))
with col3_:
    st.write("Calls required to reach $50k per year")
    st.write(get_pricing_values(price_dict=pricing, revenue=50000, upfront_cost=Upfront_Payment, r=Royalties))
with col4_:
    st.write("Calls required to reach $100k per year")
    st.write(get_pricing_values(price_dict=pricing, revenue=100000, upfront_cost=Upfront_Payment, r=Royalties))
with col5_:
    st.write("Calls required to reach ${0} per year".format(Desired_revenue))
    st.write(get_pricing_values(price_dict=pricing, revenue=Desired_revenue, upfront_cost=Upfront_Payment, r=Royalties))



def get_data(platform, r, upfront):
    price = pricing[platform]
    
    if platform == "Here":
        
        revenue = [upfront + price*1000*r for i in range(1,1001,sample)]
        cost_i = [price*1000 for i in range(0,1001,sample)]
        c_f = lambda x : 1.21*x
        cost = list(map(c_f, range(1001,4*10**6+1,sample)))
        revenue =  revenue + [upfront + r*i for i in cost]
        cost = cost_i + cost
        
    else:
        c_f = lambda x : price*x
        cost = list(map(c_f, range(1,4*10**6+1,sample)))
        revenue = [upfront + r*i for i in cost]
        
    df = pd.DataFrame(list(zip(range(0,4*10**6+1,sample), cost, revenue)), columns = ["Calls_1k", "Cost_to_dev", "Revenue_to_us"])
    df["Provider"] = platform
    
    return df

def create_dataset(platform = pricing.keys(), r = 0.05, upfront = 0):
    ls = []
    for i in platform:
        ls.append(get_data(platform=i, r = r, upfront=upfront))
        
    return pd.concat(ls)

ndf = create_dataset(r=Royalties/100, upfront=Upfront_Payment)


n_1 = alt.selection(type='single', nearest=True, on='mouseover',fields=['Calls_1k'], empty='none')

c = alt.Chart(ndf, height=800).mark_line(interpolate='basis').encode(
    x=alt.X('Calls_1k', axis=alt.Axis( title='1k Calls Made')),
    y=alt.Y('Revenue_to_us', axis=alt.Axis(title='Revenue Made ($)')),
    color='Provider',
    # strokeDash='Provider'
)

selectors = alt.Chart(ndf).mark_point().encode(
    x='Calls_1k',
    opacity=alt.value(0),
).add_selection(n_1)

points = c.mark_point().encode(
    opacity=alt.condition(n_1, alt.value(1), alt.value(0))
)

text = c.mark_text(align='right', dx=-15, dy=-15, ).encode(text=alt.condition(n_1, 'Revenue_to_us', alt.value(''))
)

rules = alt.Chart(ndf).mark_rule(color='gray').encode(
    x='Calls_1k',
).transform_filter(
    n_1
)

lines = [alt.Chart(pd.DataFrame({'y': [i]})).mark_rule(strokeDash=[10, 10]).encode(y='y', tooltip = ['y']).interactive() for i in [25000, 50000, 100000, Desired_revenue]]

l = alt.layer(c, selectors, points, rules, lines[0], lines[1], lines[2], lines[3], text)

st.altair_chart(l, use_container_width=True)

st.header("Client Calculator")
st.subheader("Comapny Infomation")
st.table(p_info_df)

st.subheader("Select Number of Clients for each Size")



col1__, col2__, col3__  = st.beta_columns(3)

with col1__:
    small = st.number_input("Number of Small Clients", value=1)

with col2__:
    medium = st.number_input("Number of Medium Clients", value=1)

with col3__:
    large = st.number_input("Number of Large Clients", value=1)



cdf = calculate_client_revenue(prices=pricing, company_calls=calls_per_company_size, small=small, med=medium, large=large, r=Royalties/100)

def dummyfunc(i):
    return i

work_please = dummyfunc(6)

g = alt.Chart(cdf, height=500).mark_bar().encode(
    x=alt.X('provider', axis=alt.Axis( title='Provider', labelAngle=0)),
    y=alt.Y('sum(revenue)', axis=alt.Axis(title='Revenue Made ($)')),
    color='client_size',
    tooltip = ['client_size', 'revenue']
).properties(
    width=500
).interactive()

lines_ = [alt.Chart(pd.DataFrame({'y': [i]})).mark_rule(strokeDash=[10, 10]).encode(y='y') for i in [25000, 50000, 100000, Desired_revenue]]
pfd = alt.layer(lines_[0], lines_[1], lines_[2], lines_[3], g)
st.subheader("Revenue from Clients")
st.altair_chart(pfd , use_container_width=True)

st.subheader("Revenue from Providers")
st.table(cdf.groupby("provider").sum())

st.subheader("Clients needed per provider to make ${0} Revenue".format(str(Desired_revenue)))

_col1_, _col2_ = st.beta_columns(2)

with _col1_:
    Desired_revenue_client_calc = st.number_input("Desired revenue per year ($)", value=150000)
with _col2_:
    Royalties_client_calc = st.slider("Royalties (%)", 0.1, 10.0, 1.0, 0.025)




cn_df = calculate_client_numbers(prices=pricing, company_calls= calls_per_company_size, desired_revenue=Desired_revenue_client_calc, r=Royalties_client_calc/100)

client_r = alt.Chart(cn_df, height=500).mark_bar().encode(
    x=alt.X('provider', axis=alt.Axis( title='Provider', labelAngle=0)),
    y=alt.Y('sum(revenue)', axis=alt.Axis(title='Revenue Made ($)')),
    color='client_size',
    tooltip = ['client_size','clients']
).properties(
    width=500
).interactive()

client_n = alt.Chart(cn_df, height=500).mark_bar().encode(
    x=alt.X('provider', axis=alt.Axis( title='Provider', labelAngle=0)),
    y=alt.Y('clients', axis=alt.Axis(title='Number of Clients')),
    color='client_size',
    tooltip = ['client_size','clients']
).properties(
    width=500
).interactive()



_col1, _col2 = st.beta_columns(2)

with _col1:
    st.subheader("Revenue per Providers")
    st.altair_chart(client_r , use_container_width=True)

with _col2:
    st.subheader("Number of Clients Needed")
    st.altair_chart(client_n , use_container_width=True)

    




# with col1_:
#     st.write("Average Prices per 1k calls")
#     st.write(pd.Series(pricing, name="Pricing (USD)"))






# n_2 = alt.selection(type='single', nearest=True, on='mouseover',fields=['Revenue_to_us'], empty='none')

# d = alt.Chart(ndf).mark_line(interpolate='basis').encode(
#     x=alt.X('Calls_1k', axis=alt.Axis(title='1k Calls Made')),
#     y=alt.Y('Revenue_to_us', axis=alt.Axis(title='Revenue Made ($)')),
#     color='Provider',
#     # strokeDash='Provider'
# )

# selectors_2 = alt.Chart(ndf).mark_point().encode(
#     y='Revenue_to_us',
#     opacity=alt.value(0),
# ).add_selection(n_2)

# points_2 = d.mark_point().encode(
#     opacity=alt.condition(n_2, alt.value(1), alt.value(0))
# )

# text_2 = d.mark_text(align='left', dx=10, dy=-5).encode(
#     text=alt.condition(n_2, 'Calls_1k', alt.value(' '))
# )

# rules_2 = alt.Chart(ndf).mark_rule(color='gray').encode(
#     y='Revenue_to_us',
# ).transform_filter(
#     n_2
# )

# l_2 = alt.layer(
#     d, selectors_2, points_2, rules_2, text_2
# )




# st.altair_chart(l_2, use_container_width=True)


st.button("Re-run")
