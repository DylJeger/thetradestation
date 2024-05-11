# THE TRADE STATION
#### Video Demo: https://youtu.be/Wa5YGpMyQHE
#### A web-based application using Python, HTML, CSS, SQL, Flask and Yahoo Finance's API to display charts, apply tailored indicators, and offer execution services.

<br>
<p> Using the session library, users are required to log in to access the website. The registration page enables them to do so by inputting their email, repeating their password, and accepting the terms of use. After registration, users need to log in on the index page to access their account.


<br>
<br>
On the Analysis tab, users can input a stock ticker, select a timeframe from a range of interesting periods, and apply tailored indicators such as moving averages and a volume indicator. The data is queried from Yahoo Finance, and the indicators are dynamically created based on the data and the length entered by the users. The volume chart is plotted on another y-axis, and the colors of the bars are dynamically adjusted: green if volume increased compared to the previous day and red if volume decreased. A legend is presented to facilitate user comprehension. This part required significant effort as I had to learn about Matplotlib to display multiple pieces of information on a plot, as well as plotting data on two axes. Another significant challenge was passing the chart to the HTML once it was generated. I achieved this by using a temporary buffer with the BytesIO library and then encoding it in a format recognized by Jinja before passing it to the HTML code.

<br>
<br>
On the execution tab, users can buy and sell stocks. Checks are performed for the validity of the instruments and the size of the order. Users can decide to add more shares to their position, and the application will dynamically adjust the entry price based on the new price and quantity, as well as selling a part of their position at a time. Users are also able to sell short, short more stocks to get a newly calculated average price, and then cover a part or their entire positions. The profit and loss generated by each position are also monitored and displayed on the page. This part also required a lot of work using SQL to dynamically adjust the entries and create different queries if the users wanted to enter a position, add more to it, exit part of the position, or exit entirely.
<br>
<br>
This project was a success, and I am very proud of the result. Having only learned computer science with CS50, this project was the most complex program I have ever worked on, and I will be able to use it to perform interesting analysis and assess the performance of generated ideas.