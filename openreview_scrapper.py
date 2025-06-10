import argparse
from pathlib import Path
from random import uniform
from time import sleep
from typing import Any

from openreview import Client
from openreview.api import OpenReviewClient
import pandas as pd
from tqdm import tqdm


# got from `client.get_group(id='venues').members`
VENUES_NAMES = {
    'aaai': ('AAAI.org',),
    'acl': ('aclweb.org/ACL',),
    'aistats': ('aistat.org/AISTATS', 'aistats.org/AISTATS'),
    'coling': ('COLING.org',),
    'cvpr': ('thecvf.com/CVPR',),
    'eacl': ('eacl.org/EACL',),
    'eccv': ('thecvf.com/ECCV',),
    'emnlp': ('EMNLP',),
    'iccv': ('thecvf.com/ICCV',),
    'iclr': ('ICLR.cc',),
    'icml': ('ICML.cc',),
    'icra': ('IEEE.org/ICRA',),
    'ijcai': ('ijcai.org/IJCAI',),
    'ijcnlp': ('aclweb.org/AACL-IJCNLP',),
    # 'ijcv': ('dblp.org/journals/IJCV',),
    'kdd': ('KDD.org',),
    'naacl': ('aclweb.org/NAACL',),
    'neurips': ('NeurIPS.cc',),
    'sigchi': ('acm.org/CHI',),
    'sigdial': ('SIGDIAL.org',),
    # 'tpami': ('dblp.org/journals/PAMI',),
    'uai': ('auai.org/UAI',),
    'wacv': ('thecvf.com/WACV',),
}

DECISION_KEYS = (
    ('acceptance', 'decision'),
    ('Decision', 'decision'),
    ('Meta_Review', 'recommendation'),
)

def _save_and_download_papers(
        papers_infos: list[dict[str, Any]],
        conference: str,
        year: str,
        out_dir: str = './',
        get_pdfs: bool = False,
        client: None | Client | OpenReviewClient = None,
        ) -> None:
    # save papers to tsv files, and download pdfs if requested
    paper_info_df = pd.DataFrame(columns=['title', 'abstract_url', 'pdf_url', 'source_url'])
    abstracts_df = pd.DataFrame(columns=['title', 'abstract'])
    authors_df = pd.DataFrame(columns=['title', 'authors'])

    for paper_info in papers_infos:
        abstract = paper_info['abstract']
        authors = paper_info['authors']
        paper_id = paper_info['paper_id']
        title = paper_info['title']

        paper_info_df = pd.concat([paper_info_df, pd.Series({'title': title,
                                                             'abstract_url': f'{paper_id}',
                                                             'pdf_url': f'{paper_id}',
                                                             'source_url': 0}).to_frame().T],
                                  ignore_index=True)

        abstracts_df = pd.concat([abstracts_df, pd.Series({'title': title,
                                                           'abstract': repr(abstract)}).to_frame().T],
                                 ignore_index=True)

        authors_df = pd.concat([authors_df, pd.Series({'title': title,
                                                       'authors': authors}).to_frame().T],
                                 ignore_index=True)

    print('\tWriting tables to files')
    save_dir = Path(out_dir) / f'{conference}' / f'{year}'
    if not save_dir.exists():
        print(f'\tCreating folder {save_dir}')
        save_dir.mkdir(parents=True)

    # if there are papers already, append to them
    if (save_dir / 'paper_info.tsv').exists():
        try:
            paper_info_df = pd.concat([pd.read_csv(save_dir / 'paper_info.tsv', sep='\t'), paper_info_df], ignore_index=True)
            abstracts_df = pd.concat([pd.read_csv(save_dir / 'abstracts.tsv', sep='\t'), abstracts_df], ignore_index=True)
            authors_df = pd.concat([pd.read_csv(save_dir / 'authors.tsv', sep='\t'), authors_df], ignore_index=True)

        except pd.errors.EmptyDataError:
            print('Empty paper_info.tsv found')

        # remove duplicates
        previous_len = len(paper_info_df)
        paper_info_df.drop_duplicates(subset=['title'], inplace=True)
        abstracts_df.drop_duplicates(subset=['title'], inplace=True)
        authors_df.drop_duplicates(subset=['title'], inplace=True)

        if len(paper_info_df) != previous_len:
            print(f'\tFound {previous_len - len(paper_info_df)} duplicates')

        if len(paper_info_df) != len(abstracts_df) or len(paper_info_df) != len(authors_df):
            print(f'\tError: different number of papers in tables: {len(paper_info_df)}, {len(abstracts_df)}, {len(authors_df)}')
            print(f'\tNo values were written for {conference} {year}')
            return

    authors_df['authors'] = authors_df['authors'].str.replace('*', '', regex=False)
    authors_df['authors'] = authors_df['authors'].str.replace(' ,', ',', regex=False)
    authors_df['authors'] = authors_df['authors'].str.replace(', and ', ', ', regex=False)
    authors_df['authors'] = authors_df['authors'].str.replace(' and ', ', ', regex=False)
    authors_df['authors'] = authors_df['authors'].str.replace(' & ', ', ', regex=False)

    paper_info_df.to_csv(save_dir / 'paper_info.tsv', sep='\t', index=False)
    abstracts_df.to_csv(save_dir / 'abstracts.tsv', sep='\t', index=False)
    authors_df.to_csv(save_dir / 'authors.tsv', sep='\t', index=False)

    # if requested, download pdfs to a subdirectory.
    if get_pdfs:
        if client is None:
            print('Cannot download pdfs without a client')
            return

        pdf_out_dir = save_dir / 'papers'
        if not pdf_out_dir.exists():
            print(f'\tCreating folder {pdf_out_dir}')
            pdf_out_dir.mkdir(parents=True)

        print('Downloading pdf files')
        with tqdm(papers_infos, unit='pdf') as pbar:
            for paper_info in pbar:
                paper_id = paper_info['paper_id']
                filename = f'{paper_id}.pdf'
                pbar.set_description(filename)
                pdf_outfile = pdf_out_dir / filename

                if not pdf_outfile.exists():
                    try:
                        pdf_binary = client.get_pdf(paper_id)
                        pdf_outfile.write_bytes(pdf_binary)

                    except:
                        tqdm.write(f'Error while trying to get pdf for {paper_id}: {paper_info["title"]}\n'
                              f'at https://openreview.net/pdf?id={paper_id}')

                    # add random sleep between api calls
                    sleep(uniform(1., 2.))


def _download_conference_info(
        client: Client | OpenReviewClient,
        conference: str,
        year: str,
        main_conference: bool = True,
        ) -> list[dict[str, Any]]:
    '''
    Main function for downloading conference metadata
    forum here means the paper id
    '''
    venues = _get_all_venues(client)
    conference_venue = VENUES_NAMES[conference.lower()]

    if main_conference:
        submissions_urls = [f'{v}/-/Submission' for v in venues for c in conference_venue if f'{c}/{year}/conference'.lower() in v.lower()]
        blind_submissions_urls = [f'{v}/-/Blind_Submission' for v in venues for c in conference_venue if f'{c}/{year}/conference'.lower() in v.lower()]

    else:
        submissions_urls = [f'{v}/-/Submission' for v in venues for c in conference_venue if f'{c}/{year}/workshop'.lower() in v.lower()]
        blind_submissions_urls = [f'{v}/-/Blind_Submission' for v in venues for c in conference_venue if f'{c}/{year}/workshop'.lower() in v.lower()]

    submissions = []
    for url, blind_url in zip(submissions_urls, blind_submissions_urls):
        # test which string returns the correct submissions
        try:
            new_submissions = client.get_all_notes(invitation=url, details='directReplies')
            sleep(uniform(1., 2.))
        except:
            print(f'Error while trying to get papers submissions for {conference} {year}')
            continue

        if len(new_submissions) > 0:
            submissions += new_submissions
            continue

        lower_url = '/'.join(url.split('/')[:-1] + [url.split('/')[-1].lower()])
        new_submissions = client.get_all_notes(invitation=lower_url, details='directReplies')
        sleep(uniform(1., 2.))
        if len(new_submissions) > 0:
            submissions += new_submissions
            continue

        new_submissions = client.get_all_notes(invitation=blind_url, details='directReplies')
        sleep(uniform(1., 2.))
        if len(new_submissions) > 0:
            submissions += new_submissions
            continue

        lower_url = '/'.join(blind_url.split('/')[:-1] + [blind_url.split('/')[-1].lower()])
        new_submissions = client.get_all_notes(invitation=lower_url, details='directReplies')
        sleep(uniform(1., 2.))
        if len(new_submissions) > 0:
            submissions += new_submissions

    if len(submissions) == 0:
        # print(f'\tNo submissions found for {conference} {year}')
        return []

    for review_end, decision_key in DECISION_KEYS:
        if len(submissions[0].details["directReplies"]) > 0:
            if 'invitation' in submissions[0].details["directReplies"][0]:
                accepted_papers = {submission.forum: submission.content for submission in submissions
                            for reply in submission.details["directReplies"]
                            if reply["invitation"].endswith(review_end) and reply["content"][decision_key] != 'Reject'}

            elif 'invitations' in submissions[0].details["directReplies"][0]:
                accepted_papers = {submission.forum: submission.content for submission in submissions
                                for reply in submission.details["directReplies"]
                                for invitation in reply["invitations"]
                                if invitation.endswith(review_end) and
                                    decision_key in reply["content"] and
                                    reply["content"][decision_key]["value"] != 'Reject'}
            else:
                accepted_papers = {}

        else:
            accepted_papers = {submission.forum: submission.content for submission in submissions}

        if len(accepted_papers) > 0:
            # we don't need to check the other decision key
            break

    if len(accepted_papers) == 0:
        # print(f'\tNo accepted papers found for {conference} {year}')
        return []

    print(f'\t{len(accepted_papers)} papers found for {conference} {year}')

    papers_infos = []
    for paper_id, paper_info in accepted_papers.items():
        if 'authors' not in paper_info:
            continue

        if isinstance(paper_info['abstract'], dict):
            abstract = paper_info['abstract']['value'].strip()
        else:
            abstract = paper_info['abstract'].strip()

        abstract = ' '.join(abstract.split())

        if isinstance(paper_info['abstract'], dict):
            authors = paper_info['authors']['value']
        else:
            authors = paper_info['authors']

        authors = ', '.join(authors)

        if isinstance(paper_info['abstract'], dict):
            title = paper_info['title']['value'].strip()
        else:
            title = paper_info['title'].strip()

        papers_infos.append({
            'abstract': abstract,
            'authors': authors,
            'paper_id': f'{paper_id}',
            'title': title,
            })

    return papers_infos


def _get_all_venues(client: OpenReviewClient) -> list[str]:
    return client.get_group(id='venues').members


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--conference', type=str, required=True,
                        choices=tuple(VENUES_NAMES.keys()), help='conference to scrape data')
    parser.add_argument('-d', '--download_pdfs', action='store_true', help='if included, download pdfs')
    parser.add_argument('-l', '--log_level', type=str, default='warning',
                        choices=('debug', 'info', 'warning', 'error', 'critical', 'print'),
                        help='log level to debug')
    parser.add_argument('-o', '--out_dir', type=Path, default=Path('data/'), help='directory where data should be saved')
    parser.add_argument('--password', default='', help='defaults to empty string (guest user)')
    parser.add_argument('--username', default='', help='defaults to empty string (guest user)')
    parser.add_argument('-w', '--include_workshops', action='store_true', help='if included, include workshops')
    parser.add_argument('-y', '--year', type=str, required=True, help='year of the conference')
    args = parser.parse_args()

    year = int(args.year)
    if year >= 2023:
        client = OpenReviewClient(baseurl='https://api2.openreview.net', username=args.username, password=args.password)
    else:
        client = Client(baseurl='https://api.openreview.net', username=args.username, password=args.password)

    print('Getting openreview metadata for main conference')

    papers_infos = _download_conference_info(client, args.conference, args.year, main_conference=True)

    if len(papers_infos) == 0:
        print(f'\tNo data found for main conference {args.conference} {args.year}')

    if args.include_workshops:
        print('Getting openreview metadata for workshops')
        # add random sleep between api calls
        sleep(uniform(1., 2.))
        workshop_papers_infos = _download_conference_info(client, args.conference, args.year, main_conference=False)

        if len(workshop_papers_infos) == 0:
            print(f'\tNo data found for workshops in conference {args.conference} {args.year}')
        else:
            papers_infos += workshop_papers_infos

    if len(papers_infos) > 0:
        _save_and_download_papers(papers_infos, args.conference, args.year, args.out_dir, args.download_pdfs, client)

    else:
        print(f'\tNo data found for conference {args.conference} {args.year} in openreview')
