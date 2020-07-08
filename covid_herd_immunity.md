# Introduction:

In recent months many of the southern states in the US along with some recently reopening countries have seen spikes in their COVID cases.
However places which were hit harder by coronavirus early on (in particular New York) have not seen their cases spike in the same way, even as they start to reopen.

# New York - A Case Study

Starting in the middle of February an outbreak in New York City quickly grew to massive proportions, with infections doubling approximately every 3 days.
After peaking around the start of April infections started declining with cases dropping in half roughly every two weeks. Near the end of april a random antibody 
survey revealed that ~30% of all New Yorkers had been infected, a figure which accords well with the [excess death numbers](https://www.cdc.gov/mmwr/volumes/69/wr/mm6919e5.htm) (~24,000 excess deaths at 1% fatality 
would mean ~30% were infected).

When analyzing different scenarios we need to be able to approximately explain the following facts.

* New York City's infection started off doubling every 3 days.
* The infection rate started to drop near the start of april, when roughly 15-20% of the population had been infected.
* With roughly 30% of the population infected, New York has not seen cases rise during it's partial reopening.

# R0 and Lockdowns

The R0 and SEIR model to explain this data is the story you are probably most familiar with.

In this model the infection rate is based on two factors:

* R0: How many people in a completely uninfected population the average person infects. This is based on people's behavior.
* Infected Percentage: What percentage of the population is infected.

A key concept is *herd immunity* when outbreaks peak and new outbreaks no longer grow exponentially. This point occurs when R0 * (1 - Infected Percentage) = 1.0
If we examine New York City's outbreak through this lens we can make the following conclusions.

At the start of the outbreak the R0 was [~5](https://www.medrxiv.org/content/10.1101/2020.05.17.20104653v3) (doubling every 3 days), near the end of march 
an emergency lockdown was instituted which reduced the R0 to less than 1.25[^1] cutting off the growth. Because New York is being cautious during reopening and 
has kept it's R0 under 1.5[^2] it is still not seeing spikes during the reopening.

This model has been the basis of our public policy and it is easy to see why. If New York were to return to its precovid policy infections would 
once again skyrocket, only peaking when ~40,000 more people had died[^3]. In addition it seems clear that whatever New York is doing in it's lockdown must be 
working fairly well. 

However it is important to note that even in this model the spike being observed in states like 

# Cr

[^1]: 20% infected means that if R0 is less than 1.25 infections will drop.
[^2]: 33% infected means that if R0 is less than 1.5 infections will drop.
[^3]: With an R0 of 5.0 infections will peak when 80% of the population has been infected, which would mean ~67,000 total deaths.
