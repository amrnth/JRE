from llm import LLM


def generate_summary_from_prompt():
    news_data = ""
    with open("news_shorts/data.json", encoding="utf-8") as f:
        news_data = f.read()
    

    prompt = """
    Given the following is the data about a news article. Read through it and generate a 60-words(max. 4 sentences) word summary of the news. 
    
    I aim to convert the summary into a video which looks like this:
    There will one paragraph in the summary with a background image. The background image should be chosen from one of the supplied images. You need to take into consideration the `label` and `image_contents` of the images in order to decide which image to use. Make sure to follow the following rule of number of images when considering the number of parts of the summary: 

    1. When number of images<=3, use all images in the response
    2. When number of images >3, use only 3 images

    Next, the text part of the summary should take the following into consideration:
    1. It should highlight all important points from the news
    2. It should take the article's headline into consideration 
    3. It should be concise should have atleast 90 words, and atmost 100 words.
    4. It should be coherent and not end randomly

    Output format:
    {
        "contents": [
            {
                "text": "<text of the part of the summary>",
                "image": "<link of the background image>"
            }
        ]
    }

    Input.json:\n""" + news_data+"""\n\n
    Output.json:
    """

    response = LLM.call_gemini(prompt, None)

    with open("news_shorts/response.txt", "w") as f:
        f.write(response)

if __name__ == "__main__":
    generate_summary_from_prompt()