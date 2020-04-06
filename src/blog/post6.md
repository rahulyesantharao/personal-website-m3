This past semester, I took [http://student.mit.edu/catalog/search.cgi?search=6.301](6.301), a Solid-State Circuits course that focuses on transistors and their practical applications through labs.

In this first post, I want to cover some of the fundamental single-transistor amplifiers that act as building blocks for all larger transistor-based designs.

## Single Transistor Amplifiers
Each of these three topologies has its own pros and cons, and we will cover these in detail below. They are each named "Common-*X* Amplifier". This name indicates that the *X* terminal of the transistor is common to both the input and output ends of the transistor. In practical terms, this generally means that it is shorted to the ground reference that the input and output are measured against. I will demonstrate all of the topologies with an NPN BJT, but it is good to note that any of these topologies can equivalently be used with PNP or MOSFET transistors, with similar properties.

### Common-Emitter Amplifier
In this first amplifier topology, the emitter is grounded, the input signal is applied to the base, and the output is measured at the collector.

![Common-Emitter Amplifier](assets/6/CommonEmitter.svg "Common-Emitter Amplifier")

We will use the hybrid-pi model of the BJT to do a small signal analysis of this amplifier.



