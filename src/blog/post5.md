(I taught this class at MIT Splash 2018; see the presentation [here](https://rahulyesantharao.com/blog-posts/assets/splash18_gzip.pdf "here"))

The term gzip refers to both the common UNIX command line utility for file compression as well as the file format that it uses to store compressed data files. The utility itself is based on the DEFLATE algorithm, detailed in [RFC 1951](https://www.ietf.org/rfc/rfc1951.txt), and the file format is detailed in [RFC 1952](https://www.ietf.org/rfc/rfc1952.txt). According to the RFC, the purpose of DEFLATE is to give a lossless compression format that

  > - Is independent of CPU type, operating system, file system, and character set, and hence can be used for interchange; <br/>
  > - Can be produced or consumed, even for an arbitrarily long sequentially presented input data stream, using only an a priori bounded amount of intermediate storage, and hence can be used in data communications or similar structures such as Unix filters; <br/>
  > - Compresses data with efficiency comparable to the best currently available general-purpose compression methods, and in particular considerably better than the "compress" program; <br/>
  > - Can be implemented readily in a manner not covered by patents, and hence can be practiced freely; <br/>
  > - Is compatible with the file format produced by the current widely used gzip utility, in that conforming decompressors will be able to read data produced by the existing gzip compressor. <br/>

We will cover the entire DEFLATE algorithm at a very detailed level to get a good understanding of compression methodology.

## Encoding Algorithms

All data can be thought of as represented by some alphabet, consisting of characters. As a very trivial example, we can think of English text, and of the (26 character) English alphabet as the alphabet that represents this data. As an extension upon this example, we may consider our alphabet to be the ASCII or Unicode character set, much larger alphabets that in turn allow us to represent different kinds of data. However, given the digital nature of our modern computer, alphabets cannot be directly stored into data files; they must be encoded with binary values to be saved to disk. ASCII and Unicode in fact represent not only alphabets, but also the binary encodings for these alphabets; for example, ASCII uses the encoding `0b1001110` to represent the character `N`, and the encoding `0b1111011` to represent the character `{`. Given these encodings, we are able to go from text in the English alphabet to a data file that is stored on the computer. However, one may ask for a given text file whether ASCII gives the optimal binary encoding. Is there a different option that will make the resulting text file smaller in size? As it turns out, there is almost always a better way to encode a specific piece of data, because we are able to make use of the specific frequencies of characters that appear in this data. 

In general, there are two key methods of binary data encoding: fixed-length and variable-length. ASCII is a fixed-length encoding scheme: it uses the same number of bits for every character in the alphabet, providing unambiguous and easily-interpretable data (just read every 2 bytes in). However, it is easy to see that fixed-length encodings will not perform optimally for any given piece of text. Intuitively, we would want the more frequent characters to have shorter codes and the less frequent characters to have longer codes, so that the resulting data file would be smaller on disk. Variable-length encodings leverage the actual frequencies of the characters in the data to be encoded in order to choose better encodings. The result, however, is that the encoding is highly specific to the given body of text, and must be specified along with the file in order to make it interpretable.

One key point to note about variable-length encodings is that they must have the [*prefix property*](https://en.wikipedia.org/wiki/Prefix_code): no encoding can also be the prefix of a different, longer encoding, as this would make the resulting data ambiguous.

### [Huffman Codes](https://en.wikipedia.org/wiki/Huffman_coding)

As it turns out, the problem of finding an optimal binary encoding for an alphabet, given the data to be encoded, was solved by [David A. Huffman](https://en.wikipedia.org/wiki/David_A._Huffman) in 1952. His Huffman encoding scheme provides an efficient method for generating a binary encoding based on frequencies of characters in a given text. Read about the full details of the scheme [here](https://brilliant.org/wiki/huffman-encoding/) and [here](https://www2.cs.duke.edu/csed/poop/huff/info/).

### [LZW](https://en.wikipedia.org/wiki/Lempel%E2%80%93Ziv%E2%80%93Welch)

The above discussion makes a crucial simplifying assumption, which allows for the optimality claim. In particular, it assumes that we are interested in a single-character binary encoding for the alphabet. However, if we remove this restriction, we are able to make far more efficient encodings because specific sequences of characters may repeat several times throughout the text (for example, in English, it is often beneficial to create a single code for the sequence "qu" rather than for "q" and "u" separately). This problem was also solved to optimality (in an information theoretical sense - the expected encoded length tends to the entropy bound) by [Abraham Lempel](https://en.wikipedia.org/wiki/Abraham_Lempel), [Yaakov Ziv](https://en.wikipedia.org/wiki/Yaakov_Ziv), and [Terry Welch](https://en.wikipedia.org/wiki/Terry_Welch) in 1984 in their LZW compression algorithm. There is in fact an entire family of LZ compression techniques; two earlier versions were [LZ77 and LZ78](https://en.wikipedia.org/wiki/LZ77_and_LZ78), published by Lempel and Ziv in 1977 and 1978, respectively. Read about LZW encoding [here](http://web.mit.edu/6.02/www/s2012/handouts/3.pdf) (an exceptional resource) and [here](https://www2.cs.duke.edu/csed/curious/compression/lzw.html).

Interestingly, there were some patent controversies surrounding the LZW compression algorithm throughout the late 1980s and 1990s (see bullet point 4 in the DEFLATE goals, listed above). Thus, as compression techniques were fleshed out into standard utilities, the computing community quickly ended up using the LZ77 based DEFLATE algorithm for general purpose data compression. The LZ77 algorithm is fairly similar to the LZW compression algorithm, but it keeps a sliding window for the purpose of dictionary building, rather than allowing matches from the entire preceding text. You can read about the entire LZ compression family, and the comparisons between different variations, [here](https://cs.stanford.edu/people/eroberts/courses/soco/projects/data-compression/lossless/lz77/variations.htm).

## [DEFLATE](https://en.wikipedia.org/wiki/DEFLATE)

The DEFLATE algorithm provides a specification that uses LZ77 and Huffman encoding to compress data. It is widely used, most prominently in the standard `gzip` utility.

### High Level Overview

The DEFLATE algorithm consists roughly of 3 steps: first, the original data is encoded using the LZ77 algorithm. Next, the LZ77 encoded data is encoded using Huffman coding in order to optimize the representation of this data. Finally, the actual descriptions of the Huffman codes are themselves Huffman coded to optimize the storage of these Huffman codes. The algorithm also defines three alphabets, the so-called "literal," "distance," and "code-length" alphabets, to represent specific portions of the data, as explained below.

### Step 1: LZ77

As mentioned above, in the first step, the original text data is encoded using the LZ77 algorithm described in the previous section. In order to represent this encoding, DEFLATE uses a special pair of predefined alphabets, given before. To understand them, we first have to remember the output of LZ77: the final, compressed data will consist of three types of values: either the literal byte value (`char`) that should be present at a given spot, or a pair of the form `(length, distance)`, indicating that `length` bytes should be repeated, starting from `distance` bytes previous. The DEFLATE algorithm combines the first two of these value types, literal (byte value) and length, into a single alphabet of 285 characters, specified below as the "literal" alphabet. It also defines a second "distance" alphabet (also above) of 29 characters to represent the distance values. Thus, the DEFLATE algorithm first runs LZ77 and saves the encoded data in the given alphabets. As an example, the file

    Hello World
    Hello World
    Hello World
    Hello World
    Hello World
    Hello World
    Hello World
    Hello World
    Hello World
    Hello World
    Hello World
    Hello World
    Hello World
    Hello World
    Hello World
    Hello World
    Hello World
    Hello World
    Hello World
    Hello World
    Hello World
    Hello World
    Hello World

would be encoded as

    // Symbolic Representation
    'H' 'e' 'l' 'l' 'o' ' ' 'W' 'o' 'r' 'l'
    'd' '\n' 'H' (258, 12) (5, 12) '\n' 'EOB'

    // Encoding in Literal/Distance Alphabets
    72; 101; 108; 108; 111; 32; 87; 111; 114; 108;
    100; 10; 72; (285, 6(+3)); (259, 6(+3)); 10; 256

As we see, LZ77 takes massive advantage of the repetition in the data, and it only encodes the string once in its literal form, and then it simply indicates that the previous 12 characters should be repeated several times. 

Note that the first 256 values in the literal alphabet directly map to byte (ASCII) values, and the values from 257-285 represent lengths, and have corresponding back distances. Also note that the `(+0)` type demarcations above represent the values in the extra bits of the encoding (length codes `285` and `259` have 0 extra bits). See the implementation details below for the actual alphabet values.

### Step 2: Huffman on LZW Coding

From the previous step, we have a file of data written in two interleaving alphabets. Naively, we could directly write this data down in the direct fixed-length binary encoding of the alphabet characters. However, the entire goal of DEFLATE is to minimize space usage, so we will make use of our Huffman coding knowledge to further decrease the space usage. Instead of using fixed-length binary encoding, which would necessitate 9 bits for every literal value, for example, we Huffman encode the literal and distance alphabets based on the document from the previous step, and save the data in this encoded form.

This encoding brings up a new issue, however: we must actually save and transmit the Huffman codes, as it will change with every new document (or block, as we will see later). Keeping this in mind, we move on to step 2.5.

### Step 2.5: Run Length Encoding

Directly saving every single Huffman code for every character of the alphabet would be incredibly space-inefficient, and would render meaningless any space savings we were able to make through LZ77. Because of this, DEFLATE uses a specific ordering convention for its Huffman codes. In particular, 

> - All codes of a given bit length have lexicographically
consecutive values, in the same order as the symbols
they represent;<br/>
> - Shorter codes lexicographically precede longer codes.

For example, if we are encoding A, B, C, D as 00, 011, 1, 010, we can keep the same code lengths (which are the only part that actually represent the relative frequencies of the characters and thus the space savings) but follow the given rules by instead using the codes 10, 110, 0, 111. The purpose of this rule is that we can specify the entire Huffman tree simply by giving the consecutive code lengths. For example, in our example, it is enough to say (2, 3, 1, 3) to specify the entire Huffman coding (try it out: there is only one way to follow the given rules and use the given code lengths). In particular, we can use the following code to take a set of lengths and convert them to a Huffman tree (see the repo at the end for the full function, `build_tree()`).

    #!c
    // bl_count[i]: the number of Huffman codes of length i     
    // tree[i].code: the Huffman code for alphabet value i      

    // Compute next_code (from RFC 1951, Section 3.2.2)
    code = 0;
    for(i=1; i <= MAX_HUFFMAN_LENGTH; ++i) {
        code = (code + bl_count[i-1]) << 1;
        next_code[i] = code;
    }

    // Build tree (modified from RFC 1951, Section 3.2.2)
    tmp = 0;
    for(i = 0; i < lengths[lengths_size-1].end+1; ++i) {
        tree[i].code = next_code[tree[i].len]++;
    }

As you can see, we are able to directly take the given code lengths and generate the Huffman codes from them by taking into account the prefix uniqueness of Huffman codes. 

Using this convention, we are able to compress the Huffman codes by applying a [run length encoding](https://en.wikipedia.org/wiki/Run-length_encoding) to them (essentially, instead of giving a list of code lengths in order, we give a list of runs of code lengths). For example, the RLE of (5, 5, 5, 5, 6, 6, 6, 6, 6, 6) if represented as ((5, 4), (6, 6)), because 5 is repeated 4 times and 6 is repeated 6 times. 

In order to actually represent this run-length encoding of the Huffman trees, we will make use of the code-length alphabet mentioned at the beginning. This alphabet allows us to relatively concisely represent run length encodings, because it allows us to represent the code lengths from 0-15 directly, and then give repeating sections using special characters (e.g. 16 + 2 extra bits tells us to repeat the previous code 3-6 times) - see the Alphabets section below to see the exact alphabet values.

### Step 3: Huffman on Huffman Trees

From the previous section, we have two Huffman trees represented as RLE sequences in the code-length alphabet. If we squint at this situation, we may realize it looks exactly like the beginning of Step 2 - a large length of text in some given alphabet! So, we repeat our previous strategy a second time - we will Huffman encode the code-length alphabet based on the frequencies in the RLE representations of the previous Huffman trees.

Finally, we need to specify this Huffman tree for the code-length alphabet. However, we don't want to get stuck in an infinite loop here, so we stop after this second encoding. This time, we directly record the RLE representation of the code-length alphabet with fixed-length 3-bit codes (note that this effectively restricts the Huffman codes for the code-length alphabet to 8 bits). There is one final tricky optimization at this step, to squeeze out any extra space usage. In particular, the RLE representation of the tree is given in the order (16, 17, 18, 0, 8, 7, 9, 6, 10, 5, 11, 4, 12, 3, 13, 2, 14, 1, 15), rather than in order from 0-18. This is because the authors of the DEFLATE method decided (based on analysis) that the characters were in general most likely to be used in this order, and so if, for example, the relatively unlikely code lengths of 12, 14, 1, 15 bits are not used at all in the literal and distance Huffman trees, we can simply only specify the lengths of the codes up to 13, and stop. Note that in general, the shortest and longest code lengths are the least likely, because this represents that there are outlier characters in the document, whereas most documents are fairly well distributed amongst the alphabet.

## Implementation Details

As we saw in the section above, the DEFLATE algorithm gives us the Huffman coding for a code-length alphabet, which is in turn used to represent the Huffman coding for the literal and distance alphabets. Finally, the original data is fully compressed using LZ77 compression, encoded in the literal and distance alphabets, with the specified Huffman alphabets.

There are some implementation details that we glossed over before for clarity of the algorithm; we will specify these below.

### Alphabets

RFC 1951 defines three different alphabets, used for different steps of the compression algorithm. These alphabets are given below (taken directly from the RFC).

<table>
  <caption align="bottom">Literal Alphabet</caption>
  <tr>
    <th>Code</th>
    <th>Extra Bits</th>
    <th>Represented Lengths</th>
  </tr>
  <tr><td>0-255</td><td>0</td><td>Literal Byte Value</td></tr>
  <tr><td>256</td><td>0</td><td>End of Block (EOB)</td></tr>
  <tr><td>257</td><td>0</td><td>3</td></tr>
  <tr><td>258</td><td>0</td><td>4</td></tr>
  <tr><td>259</td><td>0</td><td>5</td></tr>
  <tr><td>260</td><td>0</td><td>6</td></tr>
  <tr><td>261</td><td>0</td><td>7</td></tr>
  <tr><td>262</td><td>0</td><td>8</td></tr>
  <tr><td>263</td><td>0</td><td>9</td></tr>
  <tr><td>264</td><td>0</td><td>10</td></tr>
  <tr><td>265</td><td>1</td><td>11,12</td></tr>
  <tr><td>266</td><td>1</td><td>13,14</td></tr>
  <tr><td>267</td><td>1</td><td>15,16</td></tr>
  <tr><td>268</td><td>1</td><td>17,18</td></tr>
  <tr><td>269</td><td>2</td><td>19-22</td></tr>
  <tr><td>270</td><td>2</td><td>23-26</td></tr>
  <tr><td>271</td><td>2</td><td>27-30</td></tr>
  <tr><td>272</td><td>2</td><td>31-34</td></tr>
  <tr><td>273</td><td>3</td><td>35-42</td></tr>
  <tr><td>274</td><td>3</td><td>43-50</td></tr>
  <tr><td>275</td><td>3</td><td>51-58</td></tr>
  <tr><td>276</td><td>3</td><td>59-66</td></tr>
  <tr><td>277</td><td>4</td><td>67-82</td></tr>
  <tr><td>278</td><td>4</td><td>83-98</td></tr>
  <tr><td>279</td><td>4</td><td>99-114</td></tr>
  <tr><td>280</td><td>4</td><td>115-130</td></tr>
  <tr><td>281</td><td>5</td><td>131-162</td></tr>
  <tr><td>282</td><td>5</td><td>163-194</td></tr>
  <tr><td>283</td><td>5</td><td>195-226</td></tr>
  <tr><td>284</td><td>5</td><td>227-257</td></tr>
  <tr><td>285</td><td>0</td><td>258</td></tr>
</table>


<table>
  <caption align="bottom">Distance Alphabet</caption>
  <tr>
    <th>Code</th>
    <th>Extra Bits</th>
    <th>Represented Distances</th>
  </tr>
  <tr><td>0</td><td>0</td><td>1</td></tr>
  <tr><td>1</td><td>0</td><td>2</td></tr>
  <tr><td>2</td><td>0</td><td>3</td></tr>
  <tr><td>3</td><td>0</td><td>4</td></tr>
  <tr><td>4</td><td>1</td><td>5,6</td></tr>
  <tr><td>5</td><td>1</td><td>7,8</td></tr>
  <tr><td>6</td><td>2</td><td>9-12</td></tr>
  <tr><td>7</td><td>2</td><td>13-16</td></tr>
  <tr><td>8</td><td>3</td><td>17-24</td></tr>
  <tr><td>9</td><td>3</td><td>25-32</td></tr>
  <tr><td>10</td><td>4</td><td>33-48</td></tr>
  <tr><td>11</td><td>4</td><td>49-64</td></tr>
  <tr><td>12</td><td>5</td><td>65-96</td></tr>
  <tr><td>13</td><td>5</td><td>97-128</td></tr>
  <tr><td>14</td><td>6</td><td>129-192</td></tr>
  <tr><td>15</td><td>6</td><td>193-256</td></tr>
  <tr><td>16</td><td>7</td><td>257-384</td></tr>
  <tr><td>17</td><td>7</td><td>385-512</td></tr>
  <tr><td>18</td><td>8</td><td>513-768</td></tr>
  <tr><td>19</td><td>8</td><td>769-1024</td></tr>
  <tr><td>20</td><td>9</td><td>1025-1536</td></tr>
  <tr><td>21</td><td>9</td><td>1537-2048</td></tr>
  <tr><td>22</td><td>10</td><td>2049-3072</td></tr>
  <tr><td>23</td><td>10</td><td>3073-4096</td></tr>
  <tr><td>24</td><td>11</td><td>4097-6144</td></tr>
  <tr><td>25</td><td>11</td><td>6145-8192</td></tr>
  <tr><td>26</td><td>12</td><td>8193-12288</td></tr>
  <tr><td>27</td><td>12</td><td>12289-16384</td></tr>
  <tr><td>28</td><td>13</td><td>16385-24576</td></tr>
  <tr><td>29</td><td>13</td><td>24577-32768</td></tr>
</table>

<table>
  <caption align="bottom">Code Length Alphabet</caption>
  <tr>
    <th>Code</th>
    <th>Extra Bits</th>
    <th>Meaning</th>
  </tr>
  <tr><td>0-15</td><td>0</td><td>Code length from 0-15</td></tr>
  <tr><td>16</td><td>2</td><td>Repeat previous code 3-6 times.</td></tr>
  <tr><td>17</td><td>3</td><td>Repeat code length 0 3-10 times.</td></tr>
  <tr><td>18</td><td>7</td><td>Repeat code length 0 11-138 times.</td></tr>
</table>

All 3 alphabets consist of some basic set of characters ("code"), each of which augmented with "extra bits," which are simply a specific number of extra bits that occur after the character to specify its meaning from a given range. For example, if we see the literal code `276`, we will then have to read the following 3 bits to determine which of lengths from 59-66 it represents (`000` is 59, etc.).

Note that the fact that the code-length alphabet only has literal characters for the values ranging from 0-15 limits our Huffman codes to be only of these lengths, 0-15. This complicates the actual Huffman coding scheme used by DEFLATE, because it cannot directly use the optimal coding, but has to take into account an upper limit on code lengths. Fortunately, we do not have to consider this difficulty when implementing a decompressor, which simply has to follow the values specified in the zipped file.

### File Structure

The data is not actually represented entirely as a single large file, but is instead broken up into several (mostly) independently encoded blocks. Each block has its own Huffman encodings, based on the frequencies of the characters within this blocks. The blocks are not entirely independent because their LZ77 encodings can refer back to previous blocks with the distance parameter. As a limit, however, the LZ77 encoding used is limited to pointing back at most 32 Kb. Each block consists first of the block type, and then the Huffman tree specifications (if applicable), and then the actual LZ77 encoded data.

It wasn't mentioned before, but there are actually 3 types of blocks. The first, `btype = 00`, represents incompressible data, and it simply directly contains the uncompressed data after the block header (block type). The second, `btype=01`, represents data encoded with fixed Huffman codes. The DEFLATE specification gives some general purpose literal and distance Huffman codes that can be used if the data would do worse by specifying new Huffman trees rather than just using these predefined Huffman trees (generally the case in smaller files, where the length of the Huffman tree specification would be comparable to the length saved by using Huffman coding in the first place). In this block type, there are no Huffman tree representations, and we directly proceed to the LZ77 encoded data. Finally, the third is `btype=10`, which represents data encoded with dynamic Huffman codes. This is exactly the case discussed above, and it includes the block header, the code-length Huffman representation, the literal and distance Huffman representations, and finally, the LZ77-encoded data.

### Byte/Bit Arrangement

As RFC 1951 states, 

> Each byte is most to least significant; bytes are least to most significant<br/>
> Data elements are packed into bytes from least to most significant bit;
> - besides Huffman codes: packed starting with least significant bit 
> - Huffman codes: packed starting with most significant bit

In particular, the bytes are packed in little-endian order, but the bits within each byte are packed in LSB-MSB order, except for the Huffman codes, which must be in the opposite order so that we can read them bit by bit and compare against the Huffman tree. This is a very complicated data representation scheme, but it can be abstracted away using the code below (assuming an Intel machine, so that bytes are read in little-endian order):

    #!c
    struct deflate_stream {
        FILE *fp;
        unsigned char buf;
        unsigned char pos;
    };

    int read_bit(struct deflate_stream *stream) {
        int r;
        if(!stream->pos) { // read in new byte
            stream->pos = 0x01;
            if((r=fread(&stream->buf, 1, 1, stream->fp)) < 1) {
                perror("Error reading in read_bit");
                exit(1);
            }
        }
        int bit = (stream->buf & stream->pos)?1:0;
        stream->pos <<= 1; // advance the bit position
        return bit;
    }

    int read_bits(struct deflate_stream *stream, int n, int huffman) {      
        int i, ret = 0;
        if(huffman) {
            for(i=0; i<n; ++i) { // bit order is MSB->LSB
                ret <<= 1; 
                ret |= read_bit(stream);
            }
        }
        else {
            for(i=0; i<n; ++i) { // bit order is LSB->MSB
                ret |= (read_bit(stream) << i);
            }
        }
        return ret;
    }

As we see, `deflate_stream` allows us to read the bytes of the file in one at a time into a buffer and decode the bits in order (by masking with `pos`). Further, `read_bits` allows us to read the bits in either order, depending on whether the data we are reading represents a Huffman code or not. In this way, we can abstract away the fairly confusing data format.

### Full Implementation

See my repo [here](https://github.com/rahulyesantharao/ryunzip) to see a full implementation of a DEFLATE-compliant decompressor. By reviewing the steps taken to decompress data, you can check your understanding of the entire algorithm.
