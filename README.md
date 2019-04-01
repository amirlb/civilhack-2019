# civilhack-2019 - TheRouteAngels

This is us:

![About Us](..//master//snapshots//TheRouteAngels1.jpg)


We chose to tackle 2 challenges from the open-bus challenges in the hackathon.

![Our Goal](..//master//snapshots//TheRouteAngels2.jpg)



We built a website that let's the user enter origin and destination, and see optional public transport routes,
together with an overlay of predicted bottlenecks on the route.

![Live demo](..//master//snapshots//TheRouteAngels3.gif)


We defined a bottleneck as a geo-temporal slice of 100 m. and 10 min.,
where at least 2 buses spent at least 3 minutes in this slice.

We then define the "busy index" to be the average number of minutes
the buses spent in this geo-temporal slice.

![The Busy Index](..//master//snapshots//TheRouteAngels4.jpg)


It is also possible to visualize a bottleneck heat-map of expected traffic.

![The Busy Index](..//master//snapshots//TheRouteAngels5.gif)



And since this is is for the greater good, you can browse the documentation
[here](https://amirlb.github.io/civilhack-2019/)

![Documentation Landing Page](..//master//snapshots//TheRouteAngelsDocumentation.jpeg)
