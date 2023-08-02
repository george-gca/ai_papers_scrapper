import argparse
from pathlib import Path

import openreview
import pandas as pd
from tqdm import tqdm


def download_conference_info(client: openreview.Client, conference: str, year: str, out_dir: str = './', get_pdfs: bool = False):
    '''
    Main function for downloading conference metadata (and optionally, PDFs)
    forum here means the paper id
    '''
    print('Getting metadata')

    if conference == 'iclr':
        invitation_urls = [f'ICLR.cc/{year}/Conference/-/Blind_Submission']

        if year == '2019':
            review_end = 'Meta_Review'
            decision_key = 'recommendation'

        else:
            review_end = 'Decision'
            decision_key = 'decision'


    elif conference == 'iclr_workshop':
        review_end = 'Decision'
        decision_key = 'decision'

        if year == '2018':
            invitation_urls =  [f'{v}/-/Submission' for v in client.get_group(id='venues').members if f'ICLR.cc/{year}/Workshop' in v]

        elif year == '2019':
            invitation_urls =  [f'{v}/-/Blind_Submission' for v in client.get_group(id='venues').members if f'ICLR.cc/{year}/Workshop' in v]

        else:
            invitation_urls =  [f'{v}/-/Blind_Submission' for v in client.get_group(id='venues').members if f'ICLR.cc/{year}/Workshop' in v]


    elif conference == 'neurips':
        invitation_urls = [f'NeurIPS.cc/{year}/Conference/-/Blind_Submission']
        review_end = 'Decision'
        decision_key = 'decision'

    elif conference == 'neurips_workshop':
        invitation_urls =  [f'{v}/-/Blind_Submission' for v in client.get_group(id='venues').members if f'NeurIPS.cc/{year}/Workshop' in v]
        review_end = 'Decision'
        decision_key = 'decision'

    submissions = []
    for invitation_url in invitation_urls:
        print(f'Getting submissions for {invitation_url}')
        new_submissions = client.get_all_notes(invitation=invitation_url, details='directReplies')
        print(f'Found {len(new_submissions)} submissions')
        submissions += new_submissions

    if len(submissions) == 0:
        print(f'No submissions found for {conference} {year}')
        return

    if len(submissions[0].details["directReplies"]) > 0:
        accepted_papers = {submission.forum: submission.content for submission in submissions for reply in submission.details["directReplies"] if reply["invitation"].endswith(review_end) and reply["content"][decision_key] != 'Reject'}
    else:
        accepted_papers = {submission.forum: submission.content for submission in submissions}

    print(f'{len(accepted_papers)} accepted papers for {conference} {year}')

    # for every paper (forum), get the decision and the paper's content
    paper_info_df = pd.DataFrame(columns=['title', 'abstract_url', 'pdf_url'])
    abstracts_df = pd.DataFrame(columns=['title', 'abstract'])
    authors_df = pd.DataFrame(columns=['title', 'authors'])

    for paper_id, paper_info in accepted_papers.items():
        title = paper_info['title'].strip()
        authors = ', '.join(paper_info['authors'])
        abstract = paper_info['abstract']
        abstract = abstract.strip()
        abstract = ' '.join(abstract.split())

        paper_info_df = pd.concat([paper_info_df, pd.Series({'title': title,
                                                             'abstract_url': f'{paper_id}',
                                                             'pdf_url': f'{paper_id}'}).to_frame().T],
                                  ignore_index=True)

        abstracts_df = pd.concat([abstracts_df, pd.Series({'title': title,
                                                           'abstract': repr(abstract)}).to_frame().T],
                                 ignore_index=True)

        authors_df = pd.concat([authors_df, pd.Series({'title': title,
                                                       'authors': authors}).to_frame().T],
                                 ignore_index=True)

    print('Writing tables to files')
    save_dir = Path(out_dir) / f'{conference}' / f'{year}'
    if not save_dir.exists():
        print(f'Creating folder {save_dir}')
        save_dir.mkdir(parents=True)

    paper_info_df.to_csv(save_dir / 'paper_info.csv', sep=';', index=False)
    abstracts_df.to_csv(save_dir / 'abstracts.csv', sep='|', index=False)
    authors_df.to_csv(save_dir / 'authors.csv', sep=';', index=False)

    # if requested, download pdfs to a subdirectory.
    if get_pdfs:
        pdf_out_dir = save_dir / 'papers'
        if not pdf_out_dir.exists():
            print(f'Creating folder {pdf_out_dir}')
            pdf_out_dir.mkdir(parents=True)

        print('Downloading pdf files')
        with tqdm(accepted_papers.items(), unit='pdf') as pbar:
            for paper_id, paper_info in pbar:
                filename = f'{paper_id}.pdf'
                pbar.set_description(filename)
                pdf_outfile = pdf_out_dir / filename

                if not pdf_outfile.exists():
                    try:
                        pdf_binary = client.get_pdf(paper_id)
                        pdf_outfile.write_bytes(pdf_binary)

                    except:
                        print(
                            f'Error while trying to get pdf for {paper_id}: {paper_info["title"].strip()}\n'
                            f'at https://openreview.net/pdf?id={paper_id}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--baseurl', default='https://api.openreview.net')
    parser.add_argument('-c', '--conference', type=str, required=True,
                        choices=('iclr', 'neurips', 'neurips_workshop'),
                        help='conference to scrape data')
    parser.add_argument('-d', '--download_pdfs', action='store_true',
                        help='if included, download pdfs')
    parser.add_argument('-l', '--log_level', type=str, default='warning',
                        choices=('debug', 'info', 'warning',
                                 'error', 'critical', 'print'),
                        help='log level to debug')
    parser.add_argument('-o', '--outdir', default='data/',
                        help='directory where data should be saved')
    parser.add_argument('--password', default='',
                        help='defaults to empty string (guest user)')
    parser.add_argument('--username', default='',
                        help='defaults to empty string (guest user)')
    parser.add_argument('-y', '--year', type=str, required=True,
                        help='year of the conference')
    args = parser.parse_args()

    client = openreview.Client(
        baseurl=args.baseurl,
        username=args.username,
        password=args.password)

    download_conference_info(
        client, args.conference, args.year, args.outdir, get_pdfs=args.download_pdfs)
